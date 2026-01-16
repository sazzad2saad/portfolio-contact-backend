import os
import sqlite3
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

import resend

# Load environment variables
load_dotenv()

# Resend setup
resend.api_key = os.getenv("RESEND_API_KEY")

MY_EMAIL = os.getenv("EMAIL_USER")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

app = Flask(__name__)

# CORS: allow only your frontend
CORS(app, resources={
    r"/contact": {
        "origins": ["https://sazzad2saad.vercel.app"]
    }
})

# -------------------- DATABASE --------------------
def init_db():
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            followup_sent INTEGER DEFAULT 0
        )
    """)
    db.commit()
    db.close()

init_db()

# -------------------- ROUTES --------------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Backend is live"}), 200


@app.route("/contact", methods=["POST", "OPTIONS"], strict_slashes=False)
def contact():
    data = request.get_json(silent=True)

    print("Received data:", data)

    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    name = data.get("name")
    email = data.get("email")
    message = data.get("message")

    if not name or not email or not message:
        return jsonify({"error": "All fields are required"}), 400

    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO messages (name, email, message) VALUES (?, ?, ?)",
        (name, email, message)
    )
    db.commit()
    message_id = cursor.lastrowid

    # -------------------- EMAILS --------------------
    try:
        # Notify you
        resend.Emails.send({
            "from": "Portfolio Contact <onboarding@resend.dev>",
            "to": [MY_EMAIL],
            "reply_to": email,
            "subject": f"New Contact from {name}",
            "html": f"""
                <h2>New Contact Message</h2>
                <p><strong>Name:</strong> {name}</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Message:</strong></p>
                <p>{message}</p>
                <hr>
                <small>
                    Message ID: {message_id}<br>
                    Received: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </small>
            """
        })

        print("Admin notification email sent")

        # Confirmation email to user
        resend.Emails.send({
            "from": "Saad.dev <onboarding@resend.dev>",
            "to": [email],
            "subject": "Thanks for contacting me!",
            "html": f"""
                <h2>Hi {name},</h2>
                <p>Thanks for reaching out! I've received your message and will reply soon.</p>
                <blockquote>{message[:200]}</blockquote>
                <p>Best regards,<br>Saad</p>
            """
        })

        cursor.execute(
            "UPDATE messages SET followup_sent = 1 WHERE id = ?",
            (message_id,)
        )
        db.commit()

        print("User confirmation email sent")

    except Exception as e:
        print("Email error:", e)

    finally:
        db.close()

    return jsonify({"message": "Contact form submitted successfully!"}), 200


# -------------------- RUN --------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    print(f"Server running on port {port}")