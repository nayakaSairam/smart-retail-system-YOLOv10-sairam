# 🛒 Smart Retail Billing System

An end-to-end, cutting-edge smart billing system combining YOLOv10 object detection, Raspberry Pi interfacing, and UPI payments—featuring real-time product detection, weight-based validation, receipt generation, and WhatsApp delivery.

---

## 🚀 Key Features

* **🎯 Real-Time Object Detection**: Detects items instantly using a custom YOLOv10 ONNX model (`best_AR.onnx`).
* **⚖️ Weight Verification**: Validates item authenticity and fraud-prevention with load cell integration via HX711.
* **💸 Dynamic Pricing Engine**: Uses nearest-weight matching from `items.xml` for accurate pricing.
* **📊 Seamless Streamlit UI**: Cart view, quantity editing, and expense distribution graph with Plotly.
* **💳 Multi-Modal Payment**: Supports UPI (QR generation), Cash, Card—all from the frontend.
* **📱 WhatsApp Receipt**: Automatically sends a beautifully formatted digital receipt via Twilio.
* **🧾 Logging & Audit Trail**: Stores each transaction securely in `transactions.log`.

---

## 🧱 File Structure

```
SmartRetailSystem/
├── models/
│   ├── best_AR.onnx       # YOLOv10 object detection model
│   └── best.tflite        # TFLite model (future use or alternate deployment)
├── items.xml              # Product details: names, weights, prices
├── final.py               # Core script: handles detection, weighing, app launch
├── streamlit_receipt_app.py  # UI frontend: summary, UPI QR, receipt
├── hx711.py               # Load cell sensor driver (HX711 interface)
├── requirements.txt       # Required Python libraries
```

---

## 🔧 Hardware & Software Requirements

### 🔌 Hardware

* Raspberry Pi 3/4 with camera support
* Load cell sensor with HX711 amplifier
* Compatible webcam (USB or PiCam)
* Stable power supply & wiring

### 🧠 Software

* Python 3.8 or above
* Key Python libraries:

  * `ultralytics`, `opencv-python`, `RPi.GPIO`, `streamlit`, `pandas`,
  * `qrcode[pil]`, `Pillow`, `plotly`, `twilio`
* Twilio WhatsApp sandbox account
* UPI-compatible payment app

---

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/SmartRetailSystem.git
cd SmartRetailSystem
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Prepare Assets

* Place `best_AR.onnx` and `best.tflite` inside `models/`
* Customize `items.xml` to list all your products, their prices and average weights

### 4. Run the System

```bash
python final.py
```

* Use `r` to detect/register an item
* Use `q` to finalize and generate receipt + launch Streamlit app

---

## 🧭 User Flow

1. **Start Detection**: Place item under camera, press `r`
2. **Iterate**: Continue for all items
3. **Finish**: Press `q` → auto-launches UI
4. **Review & Pay**:

   * Modify quantities
   * Select payment method
   * Scan generated UPI QR
5. **Get Receipt**: Enter WhatsApp number and receive digital receipt

---

## 🔧 Customization Ideas

* 🎨 **UI Styling**: Modify Streamlit UI (e.g., add themes or logos)
* 🤖 **Model Retraining**: Update detection logic by training a new YOLOv10 model
* ✉️ **Alternate Channels**: Replace Twilio with email/SMS
* 🧪 **Demo Mode**: Add a simulation flag for presentations

---

## 🤝 Contributing

1. Fork this repo
2. Create a new branch: `git checkout -b feature/YourFeature`
3. Make changes and commit: `git commit -m "Added a new feature"`
4. Push to GitHub: `git push origin feature/YourFeature`
5. Submit a Pull Request 🚀

---

## 📄 License

MIT License. See the [LICENSE](LICENSE) file for more info.

---

> Built with ❤️ by [Arjun Manoj](https://www.linkedin.com/in/arjun-manoj-2aa449251/) and [N Sai Ram](https://www.linkedin.com/in/sai-ram-999b26280/).
