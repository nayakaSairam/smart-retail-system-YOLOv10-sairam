import time
import cv2
from ultralytics import YOLO
from collections import defaultdict
import RPi.GPIO as GPIO
from hx711 import HX711
import xml.etree.ElementTree as ET
import subprocess
import json
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load the YOLO model
MODEL_PATH = '/home/rpi/tflite-custom-object-bookworm-main/best_AR.onnx'  # Replace with your model path
model = YOLO(MODEL_PATH, task="detect")

def initialize_hx711():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    dout_pin = 27  # Replace with your DOUT_PIN if different
    pd_sck_pin = 17  # Replace with your PD_SCK_PIN if different
    return HX711(dout_pin=dout_pin, pd_sck_pin=pd_sck_pin)

def round_to_nearest_five(x):
    return 5 * round(x / 5)

def calibrate_sensor(hx):
    try:
        logging.info("Taring the scale (zeroing)...")
        hx.zero()
        
        input("Place a known weight on the scale and press Enter...")
        reading = hx.get_data_mean()
        
        if reading:
            logging.info(f"Mean value from HX711 (raw reading): {reading}")
            known_weight_grams = float(input('Enter the known weight in grams: '))
            ratio = reading / known_weight_grams
            hx.set_scale_ratio(ratio)
            logging.info(f"Calibration successful! Ratio is set to {ratio}")
            return ratio
        else:
            logging.error("Failed to read mean value. Calibration aborted.")
            return None
    except Exception as e:
        logging.error(f"Calibration failed: {str(e)}")
        return None

def load_prices_from_xml(xml_file):
    prices = defaultdict(list)
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        for item in root.findall('item'):
            name = item.get('name')
            weight = int(item.get('weight'))
            price = float(item.get('price'))
            sold_by_weight = item.get('sold_by_weight', 'false').lower() == 'true'
            prices[name].append({
                "weight": weight,
                "price": price,
                "sold_by_weight": sold_by_weight
            })
        logging.info(f"Loaded prices: {dict(prices)}")
    except Exception as e:
        logging.error(f"Error reading XML file: {e}")
    return prices

def calculate_total_price_with_nearest_weight(object_data, prices):
    total_price = 0.0
    receipt = []
    for object_key, data in object_data.items():
        object_name, detected_weight = object_key.rsplit('_', 1)
        detected_weight = int(detected_weight)
        matched = False

        logging.info(f"Processing {object_name} with detected weight {detected_weight}g")

        if object_name in prices:
            # Get the list of available weights for the item from the XML
            weight_price_list = prices[object_name]
            # Find the price data with the nearest weight
            nearest_price_data = min(weight_price_list, key=lambda x: abs(x['weight'] - detected_weight))
            actual_weight = nearest_price_data["weight"]
            object_price = nearest_price_data["price"]
            sold_by_weight = nearest_price_data.get('sold_by_weight', False)

            if sold_by_weight:
                # For items sold by weight
                item_total = detected_weight * object_price
                receipt.append({
                    "name": object_name,
                    "weight": detected_weight,
                    "count": data['count'],
                    "price_per_gram": object_price,
                    "total_price": item_total,
                    "sold_by_weight": True
                })
                logging.info(f"Calculated price for {object_name} sold by weight: {item_total} Rs")
            else:
                # For items sold per unit
                object_count = data['count']
                item_total = object_count * object_price
                receipt.append({
                    "name": object_name,
                    "detected_weight": detected_weight,
                    "actual_weight": actual_weight,
                    "count": object_count,
                    "price_per_item": object_price,
                    "total_price": item_total,
                    "sold_by_weight": False
                })
                logging.info(f"Matched {object_name} to weight {actual_weight}g with price {object_price} Rs")

            total_price += item_total
            matched = True

        if not matched:
            logging.warning(f"No price found for {object_name} with detected weight {detected_weight}g")
            receipt.append({
                "name": object_name,
                "weight": detected_weight,
                "count": data['count'],
                "price_per_item": 0,
                "total_price": 0,
                "message": "Price not found"
            })

    return total_price, receipt

def save_receipt_as_json(receipt, total_price):
    receipt_data = {
        "total_price": total_price,
        "items": receipt
    }
    with open("receipt.json", "w") as f:
        json.dump(receipt_data, f, indent=2)
    logging.info(f"Receipt saved to receipt.json")

def run_streamlit_app():
    """Function to run the Streamlit app synchronously."""
    subprocess.run(["streamlit", "run", "streamlit_receipt_app.py"])
    # The main program will continue after the Streamlit app is closed

def main():
    while True:
        # Step 1: Initialize the weight sensor and calibrate
        hx = initialize_hx711()
        logging.info("Calibrating the weight sensor...")
        ratio = calibrate_sensor(hx)

        if not ratio:
            logging.error("Calibration failed. Exiting.")
            return

        # Step 2: Load item prices from XML
        prices = load_prices_from_xml("items.xml")
        
        # Step 3: Open the camera for object detection
        cap = cv2.VideoCapture(0)
        object_data = defaultdict(lambda: {'count': 0, 'total_weight': 0})

        while True:
            ret, frame = cap.read()
            if not ret:
                logging.error("Error reading from camera.")
                break

            results = model(frame)
            cv2.imshow("YOLOv8 Inference", results[0].plot())
            key = cv2.waitKey(1) & 0xFF

            if key == ord('r'):
                detection_counts = defaultdict(int)
                for r in results:
                    for box in r.boxes:
                        class_name = model.names[int(box.cls[0])]
                        detection_counts[class_name] = 1  # Count all detections of the same class as 1 item

                if len(detection_counts) > 1:
                    logging.warning("Two or more different objects detected. Remove one to add to the cart and continue.")
                    continue

                # Get weight measurement
                reading = hx.get_data_mean()
                if reading is None:
                    logging.error("Failed to get weight measurement.")
                    continue
                weight = round_to_nearest_five(reading / ratio)

                # Add detected object to the cart as one item
                for class_name, count in detection_counts.items():
                    unique_key = f"{class_name}_{weight}"
                    if object_data[unique_key]['count'] == 0:
                        object_data[unique_key]['count'] = 1  # Consider multiple detections of same class as 1 item
                    object_data[unique_key]['total_weight'] = weight

                logging.info(f"Detected objects: {detection_counts}, weight: {weight} grams")

            if key == ord('q'):
                # Step 4: Calculate total price, save receipt, and launch Streamlit app for payment
                total_price, receipt = calculate_total_price_with_nearest_weight(object_data, prices)
                save_receipt_as_json(receipt, total_price)

                logging.info(f"Final object data: {json.dumps(object_data, indent=2)}")
                logging.info(f"Calculated receipt: {json.dumps(receipt, indent=2)}")

                # Release resources before launching Streamlit
                cap.release()
                GPIO.cleanup()
                cv2.destroyAllWindows()

                # Step 5: Run Streamlit app synchronously
                run_streamlit_app()

                # After Streamlit app closes, reset object data for the next customer
                object_data = defaultdict(lambda: {'count': 0, 'total_weight': 0})

                # Re-initialize the camera
                cap = cv2.VideoCapture(0)

                logging.info("Returning to object detection for new customers.")

                break  # Exit detection loop and return to main loop for new customer

if __name__ == "__main__":
    main()
