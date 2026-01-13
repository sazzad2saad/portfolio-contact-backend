import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

db = sqlite3.connect(DB_PATH)
cursor = db.cursor()

cursor.execute("SELECT * FROM messages")
rows = cursor.fetchall()

for row in rows:
    print(row)

db.close()
