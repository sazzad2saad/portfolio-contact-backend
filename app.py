import os
import sqlite3
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS

from send_email import send_followup_email

from dotenv import load_dotenv
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

app = Flask(__name__)
CORS(app)

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

@app.route("/contact", methods=["POST"])
def contact():
    data = request.get_json()  # Use get_json since frontend sends JSON

    # Validate fields and trim spaces
    if not data or not data.get("name", "").strip() or not data.get("email", "").strip() or not data.get("message", "").strip():
        return jsonify({"error": "All fields are required"}), 400

    name = data["name"].strip()
    email = data["email"].strip()
    message = data["message"].strip()

    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()

    # Insert into DB
    cursor.execute(
        "INSERT INTO messages (name, email, message) VALUES (?, ?, ?)",
        (name, email, message)
    )
    db.commit()
    message_id = cursor.lastrowid

    # Send follow-up email if keys exist
    try:
        send_followup_email(email, name)
        cursor.execute(
            "UPDATE messages SET followup_sent = 1 WHERE id = ?",
            (message_id,)
        )
        db.commit()
    except Exception as e:
        print("Email failed:", e)

    db.close()

    return jsonify({"message": "Contact form submitted successfully!"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
