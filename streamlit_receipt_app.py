import json
import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from PIL import Image
import plotly.graph_objects as go
import os
import subprocess
from datetime import datetime
import logging
from twilio.rest import Client
import traceback

# Twilio Credentials (Replace placeholders with your actual credentials)
TWILIO_ACCOUNT_SID = 'AC21e0482fbd35d389f7c8555699319c8c'  # Replace with your Account SID
TWILIO_AUTH_TOKEN = '90d26056e98a492f289c3845197df0ba'     # Replace with your Auth Token
TWILIO_WHATSAPP_FROM = 'whatsapp:+14155238886'             # Twilio Sandbox WhatsApp number

# UPI ID configuration
UPI_ID = "sairam30524@oksbi"  # Replace with your actual UPI ID
PAYEE_NAME = "SA Supermart"   # Replace with your actual payee name

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_pie_chart(df):
    fig = go.Figure(data=[go.Pie(labels=df['Item'], values=df['Total Price (Rs)'], hole=.3)])
    fig.update_layout(title_text="Distribution of Expenses")
    return fig

def send_whatsapp_message(to_number, message_body):
    account_sid = TWILIO_ACCOUNT_SID
    auth_token = TWILIO_AUTH_TOKEN
    from_whatsapp_number = TWILIO_WHATSAPP_FROM
    client = Client(account_sid, auth_token)

    # Debugging statements
    logging.info("Attempting to send WhatsApp message...")
    logging.info(f"To: {to_number}")
    logging.info(f"Message Body:\n{message_body}")

    try:
        message = client.messages.create(
            from_=from_whatsapp_number,
            body=message_body,
            to=f'whatsapp:{to_number}'
        )
        logging.info(f"Message SID: {message.sid}")
        return message.sid
    except Exception as e:
        error_message = f"Failed to send WhatsApp message: {e}\n{traceback.format_exc()}"
        logging.error(error_message)
        return None

def format_receipt_message(receipt_data, payee_name):
    total_price_updated = receipt_data.get("total_price", 0.0)
    edited_items = receipt_data.get("items", [])

    message_lines = []
    message_lines.append("🛒 *Thank you for your purchase!*")
    message_lines.append("")
    message_lines.append("*Receipt:*")
    message_lines.append("")

    for item in edited_items:
        item_name = item['name']
        item_total = item['total_price']
        if item.get('sold_by_weight', False):
            quantity = f"{item.get('weight', item.get('detected_weight', 0))} g"
            price_per_unit = f"Rs. {item['price_per_gram']}/g"
        else:
            quantity = f"{item['count']} pcs"
            price_per_unit = f"Rs. {item['price_per_item']}/pc"

        item_message = f"*{item_name}*"
        item_message += f"\nQuantity: {quantity}"
        item_message += f"\nPrice: {price_per_unit}"
        item_message += f"\nTotal: Rs. {item_total:.2f}"
        message_lines.append(item_message)
        message_lines.append("")  # Add an empty line between items

    message_lines.append(f"*Total Amount Paid: Rs. {total_price_updated:.2f}*")
    message_lines.append("")
    message_lines.append("_Visit us again!_")
    message_lines.append("")
    message_lines.append(f"*{payee_name}*")

    message_body = '\n'.join(message_lines)
    return message_body

def main():
    # Set page configuration
    st.set_page_config(
        page_title="Smart Checkout System",
        page_icon="🛒",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom CSS to enhance the UI
    st.markdown("""
        <style>
        .big-font {
            font-size:20px !important;
            font-weight: bold;
        }
        .footer {
            text-align: center;
            margin-top: 50px;
            color: #666666;
        }
        </style>
        """, unsafe_allow_html=True)

    # Header
    st.title("Smart Checkout System")

    # Initialize session state variables
    if 'generate_qr' not in st.session_state:
        st.session_state.generate_qr = False
    if 'payment_done' not in st.session_state:
        st.session_state.payment_done = False

    # Debug: Print session state
    st.write(f"Debug: generate_qr = {st.session_state.generate_qr}, payment_done = {st.session_state.payment_done}")

    # Load receipt data from JSON file
    if os.path.exists("receipt.json"):
        with open("receipt.json", "r") as f:
            receipt_data = json.load(f)
    else:
        st.error("No receipt data found.")
        return

    # Retrieve items from the receipt data
    items = receipt_data.get("items", [])

    # Initialize variables
    edited_items = []
    total_price_updated = 0.0

    # Display Items in Detail with Quantity Editing
    st.subheader("Items in Your Cart")
    st.markdown('<div class="receipt-container">', unsafe_allow_html=True)

    # Determine the number of columns
    num_columns = 3
    columns = st.columns(num_columns)
    for index, item in enumerate(items):
        col = columns[index % num_columns]
        with col:
            item_name = item['name']
            item_weight = item.get('weight', 0)
            detected_weight = item.get('detected_weight', 0)
            actual_weight = item.get('actual_weight', 0)
            price_per_item = item.get('price_per_item', 0.0)
            price_per_gram = item.get('price_per_gram', 0.0)
            sold_by_weight = item.get('sold_by_weight', False)
            total_price_item = item.get('total_price', 0.0)

            st.markdown(f"<div class='item-name big-font'>{item_name}</div>", unsafe_allow_html=True)
            st.markdown('<div class="item-details">', unsafe_allow_html=True)

            if sold_by_weight:
                # Items sold by weight
                weight = item_weight or detected_weight or actual_weight
                st.write(f"Weight: **{weight} g**")
                st.write(f"Price per gram: **{price_per_gram} Rs**")
                total_price_item = weight * price_per_gram
                st.write(f"Item Total: **{total_price_item:.2f} Rs**")
                item['weight'] = weight  # Update weight
            else:
                # Items sold per piece - Allow quantity editing
                item_count = st.number_input(
                    f"Quantity for {item_name}",
                    min_value=0,
                    value=int(item.get('count', 1)),
                    key=f"item_{index}_count",
                    step=1,
                    format="%d"
                )
                st.write(f"Price per item: **{price_per_item} Rs**")
                total_price_item = item_count * price_per_item
                st.write(f"Item Total: **{total_price_item:.2f} Rs**")
                item['count'] = item_count  # Update count

            st.markdown('</div>', unsafe_allow_html=True)

            # Update totals
            total_price_updated += total_price_item
            item['total_price'] = total_price_item
            edited_items.append(item)

    st.markdown('</div>', unsafe_allow_html=True)

    # Summary Table for Cross-Checking
    st.subheader("Summary Table")
    # Create a DataFrame for the table
    df = pd.DataFrame(edited_items)

    # Prepare data for the table
    df_table = df.copy()
    df_table['Price per Unit (Rs)'] = df_table.apply(
        lambda row: row['price_per_gram'] if row.get('sold_by_weight', False) else row['price_per_item'],
        axis=1
    )
    df_table['Quantity'] = df_table.apply(
        lambda row: f"{row.get('weight', row.get('detected_weight', 0))} g" if row.get('sold_by_weight', False) else int(row['count']),
        axis=1
    )
    df_table = df_table[['name', 'Quantity', 'Price per Unit (Rs)', 'total_price']]
    df_table = df_table.rename(columns={
        'name': 'Item',
        'total_price': 'Total Price (Rs)'
    })

    # Display the table
    st.markdown('<div class="receipt-container">', unsafe_allow_html=True)
    st.table(df_table.style.format({'Price per Unit (Rs)': '{:.2f}', 'Total Price (Rs)': '{:.2f}'}))
    st.markdown('</div>', unsafe_allow_html=True)

    # Display the updated total price
    st.markdown(f"<p class='total-price big-font'>Total Amount: {total_price_updated:.2f} Rs</p>", unsafe_allow_html=True)

    # Create and display pie chart
    st.subheader("Expense Distribution")
    fig = create_pie_chart(df_table)
    st.plotly_chart(fig)

    # Payment section
    st.markdown("### Payment Options")
    payment_method = st.selectbox("Choose a payment method", ["Cash", "Credit Card", "Mobile Payment"])

    # Collect customer's WhatsApp number
    st.markdown("### Receive Receipt via WhatsApp")
    customer_whatsapp = st.text_input("Enter your WhatsApp number (with country code)", value="+91", help="Example: +919876543210")

    
    if st.button("Proceed to Payment", key="pay_now", help="Click to proceed to payment"):
        st.session_state.generate_qr = True

    # If "Proceed to Payment" is clicked, generate the UPI-based QR code
    if st.session_state.generate_qr and not st.session_state.payment_done:
        st.write("Debug: Generating QR code")
        # UPI QR code format
        upi_payment_string = f"upi://pay?pa={UPI_ID}&pn={PAYEE_NAME}&am={total_price_updated:.2f}&cu=INR"

        # Generate the QR code with the UPI payment string
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(upi_payment_string)
        qr.make(fit=True)

        # Create an image for the QR code
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")

        # Display the QR code
        st.image(Image.open(buffered), caption="Scan this QR code to pay via UPI", width=300)

        # Show the "Payment Done" button after the QR code is generated
        if st.button("Payment Done", key="payment_done", help="Click if payment is completed"):
            st.session_state.payment_done = True
    if st.session_state.generate_qr and  st.session_state.payment_done:
        st.write("Debug: Payment Done button clicked")
        st.balloons()
        st.success("Payment Confirmed! Thank you for shopping with us.")

        # Log the transaction
        transaction_log = {
            "datetime": datetime.now().isoformat(),
            "total_price": total_price_updated,
            "payment_method": payment_method,
            "items": edited_items
        }
        with open("transactions.log", "a") as log_file:
            log_file.write(json.dumps(transaction_log) + "\n")

        # Save the updated receipt data
        receipt_data = {
            'total_price': total_price_updated,
            'items': edited_items
        }
        with open("receipt.json", "w") as f:
            json.dump(receipt_data, f, indent=2)

            # Send WhatsApp message
        if customer_whatsapp.strip() != "":
            message_body = format_receipt_message(receipt_data, PAYEE_NAME)
            message_sid = send_whatsapp_message(customer_whatsapp.strip(), message_body)
            if message_sid:
                st.success("Receipt sent via WhatsApp.")
            else:
                st.error("Failed to send receipt via WhatsApp.")
        else:
            st.warning("No WhatsApp number provided. Receipt not sent via WhatsApp.")

        st.warning("Returning to object detection for new customers...")
        # Reset the session state for the next customer
        st.session_state.generate_qr = False
        st.session_state.payment_done = False
        # Stop the Streamlit app
        subprocess.run(["python3", "/home/rpi/Desktop/Project/Weight_sensor/final.py"])
        st.stop()

    # Footer
    st.markdown(f'<div class="footer">© 2023 {PAYEE_NAME}</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
