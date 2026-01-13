import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import os

sender_email = os.getenv("EMAIL_USER")
sender_password = os.getenv("EMAIL_PASS")


def send_followup_email(to_email, name):
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")  # Gmail App Password

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = "Thank you for contacting me!"

    body = f"""
Hi {name},

Thanks for reaching out! I’ll get back to you shortly.

Best,
Saad
"""
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
