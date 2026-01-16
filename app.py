import os
import sqlite3
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS

from send_email import send_followup_email

from dotenv import load_dotenv
load_dotenv()

import resend
resend.api_key = os.getenv("RESEND_API_KEY")


my_email = os.getenv("EMAIL_USER")
sender_password = os.getenv("EMAIL_PASS")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

app = Flask(__name__)
CORS(app, resources={
    r"/contact": {
        "origins": ["https://sazzad2saad.vercel.app"]
    }
})


def init_db():
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            followup_sent INTEGER DEFAULT 0

        )
    ''')
    db.commit()
    db.close()
init_db()

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Backend is live"}), 200

@app.route("/contact", methods=["POST", "OPTIONS"], strict_slashes=False)
def contact():
    data = request.get_json(force=True)

    print("Received data:", data)

    if not data or not data.get("name") or not data.get("email") or not data.get("message"):
        return jsonify({"error": "All fields are required"}), 400

    name = data["name"]
    email = data["email"]
    message = data["message"]

    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO messages (name, email, message) VALUES (?, ?, ?)",
        (name, email, message)
    )
    db.commit()
    message_id = cursor.lastrowid

    # try:
    #     send_followup_email(email, name)

    #     cursor.execute(
    #         "UPDATE messages SET followup_sent = 1 WHERE id = ?",
    #         (message_id,)
    #     )
    #     db.commit()

    # except Exception as email_error:
    #     print("Email failed:", email_error)
    try:
        # Send notification email to yourself using Resend
        resend.Emails.send({
            "from": f"Supply Sense Contact Form <onboarding@resend.dev>",
            "to": my_email,  # Your email address
            "reply_to": email,  # User's email for reply
            "subject": f"Supply Sense Contact Request from {name}",
            "html": f"""
                <h2>New Supply Sense Contact Request</h2>
                <p><strong>Name:</strong> {name}</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Company:</strong> {company if company else 'N/A'}</p>
                <p><strong>Message:</strong> {message}</p>
                <hr>
                <p><small>Message ID: {message_id} | Received: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
            """,
        })
        
        print("Notification email sent successfully")

        # Optional: Send a confirmation email to the user
        try:
            resend.Emails.send({
                "from": f"Supply Sense <onboarding@resend.dev>",
                "to": [email],
                "subject": "We've received your message!",
                "html": f"""
                    <h2>Thank you for contacting Supply Sense!</h2>
                    <p>Hi {name},</p>
                    <p>We've received your message and will get back to you as soon as possible.</p>
                    <p><strong>A quick summary of your message:</strong></p>
                    <blockquote>{message[:200]}...</blockquote>
                    <p>We typically respond within 1-2 business days.</p>
                    <hr>
                    <p><small>This is an automated confirmation. Please do not reply to this email.</small></p>
                """,
            })
            print("Confirmation email sent to user")
            
            # Update database to mark followup sent
            cursor.execute(
                "UPDATE messages SET followup_sent = 1 WHERE id = ?",
                (message_id,)
            )
            db.commit()
            
        except Exception as followup_error:
            print("Confirmation email failed, but notification was sent:", followup_error)

    except Exception as email_error:
        print("Notification email failed:", email_error)
        # Continue even if email fails - we still saved to database
        # You might want to log this error for debugging

    return jsonify({"message": "Contact form submitted successfully!"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
