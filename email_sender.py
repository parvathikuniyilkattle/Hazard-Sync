import smtplib
import pandas as pd
import streamlit as st

from email.message import EmailMessage
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
SUBSCRIBER_FILE = BASE_DIR / "subscribers.csv"


def send_emergency_alert_email(
    alert_title,
    affected_area,
    emergency_type,
    priority,
    instructions
):

    if not SUBSCRIBER_FILE.exists():
        return False, "Subscriber file not found."

    subscribers = pd.read_csv(SUBSCRIBER_FILE)

    if subscribers.empty:
        return False, "No registered email subscribers."

    sender_email = st.secrets["gmail"]["sender_email"]
    app_password = st.secrets["gmail"]["app_password"]

    sent_count = 0

    for email in subscribers["email"].dropna():

        message = EmailMessage()

        message["Subject"] = f"HazardSync Emergency Alert: {alert_title}"
        message["From"] = sender_email
        message["To"] = email

        message.set_content(f"""
HAZARDSYNC - EMERGENCY ALERT

Alert: {alert_title}
Affected Area: {affected_area}
Emergency Type: {emergency_type}
Priority: {priority}

Instructions:
{instructions}

Please follow the instructions and stay safe.

- HazardSync Team
""")

        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(sender_email, app_password)
                server.send_message(message)

            sent_count += 1

        except Exception as error:
            print(f"Email failed for {email}: {error}")

    return True, f"Emails sent successfully to {sent_count} subscribers."