from flask import Flask, request, jsonify, render_template
import sqlite3
import threading
import time
from datetime import datetime
from plyer import notification
import os  # Import for cross-platform sound alerts

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect("reminders.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS reminders
                      (id INTEGER PRIMARY KEY, title TEXT, description TEXT, time TEXT)''')
    conn.commit()
    conn.close()

# Function to add a reminder
@app.route("/add", methods=["POST"])
def add_reminder():
    data = request.json
    title = data.get("title")
    desc = data.get("description", "")
    rem_time = data.get("time")
    if title and rem_time:
        conn = sqlite3.connect("reminders.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO reminders (title, description, time) VALUES (?, ?, ?)",
                       (title, desc, rem_time))
        conn.commit()
        conn.close()
        return jsonify({"message": "Reminder added successfully!"}), 201
    return jsonify({"error": "Title and Time are required!"}), 400

# Function to display notifications with sound
def check_reminders():
    while True:
        now = datetime.now().strftime("%H:%M")
        conn = sqlite3.connect("reminders.db")
        cursor = conn.cursor()
        cursor.execute("SELECT title, description FROM reminders WHERE time = ?", (now,))
        reminders = cursor.fetchall()
        conn.close()
        for title, desc in reminders:
            notification.notify(
                title=f"Reminder: {title}",
                message=desc if desc else "It's time!",
                timeout=10
            )
            # Cross-platform sound alert
            try:
                if os.name == "nt":
                    os.system("powershell -c (New-Object Media.SoundPlayer 'C:\\Windows\\Media\\notify.wav').PlaySync();")
                else:
                    os.system("aplay /usr/share/sounds/freedesktop/stereo/message.oga" if os.path.exists("/usr/share/sounds/freedesktop/stereo/message.oga") else "echo -e '\a'")
            except Exception as e:
                print("Sound alert failed:", e)
        time.sleep(60)

# Function to get all reminders
@app.route("/reminders", methods=["GET"])
def get_reminders():
    conn = sqlite3.connect("reminders.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, time FROM reminders")
    reminders = cursor.fetchall()
    conn.close()
    return jsonify(reminders)

# Home Route
@app.route("/")
def home():
    return render_template("index.html")

# Start reminder checking thread
init_db()
th = threading.Thread(target=check_reminders, daemon=True)
th.start()

if __name__ == "__main__":
    app.run(debug=True)
