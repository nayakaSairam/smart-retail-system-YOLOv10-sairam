# --------------------------------------------
# Install and Import Required Libraries
# --------------------------------------------
# !pip install ultralytics  # Uncomment if running for the first time

from IPython import display
display.clear_output()

import ultralytics
ultralytics.checks()  # Verify installation and environment

from ultralytics import YOLO
import torch
import os

# Check if CUDA is available
print("CUDA Available:", torch.cuda.is_available())

# --------------------------------------------
# Load YOLOv10n Model
# --------------------------------------------
# Make sure yolov10n.pt is available in your working directory
model = YOLO("yolov10n.pt")  # You can replace this with your custom model path if needed
model.info()

# --------------------------------------------
# To Train the Model (Uncomment and Configure)
# --------------------------------------------
# model.train(
#     data="path/to/your/data.yaml", 
#     epochs=100, 
#     imgsz=640
# )

# --------------------------------------------
# Run Inference on a Folder of Images
# --------------------------------------------
test_images_dir = "path/to/test/images"  # Replace with actual path to your test images

# Loop through all valid image files and run inference
for image_name in os.listdir(test_images_dir):
    if image_name.lower().endswith(('.jpg', '.jpeg', '.png')):
        image_path = os.path.join(test_images_dir, image_name)
        results = model(image_path, save=True)  # Save results to runs/detect

print("Inference completed.")
