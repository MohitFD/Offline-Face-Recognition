import requests
import json
import sqlite3
from datetime import datetime

# Import DB_PATH from database.py
from database import DB_PATH, init_db

def save_session(data):
    """Save session data to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO sessions (token, employee_id, name, email, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (data["token"], data["employee_id"], data["name"], data["email"], datetime.utcnow())
    )
    conn.commit()
    conn.close()

def load_session():
    """Load session data from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT token, employee_id, name, email FROM sessions LIMIT 1
        """
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "token": row[0],
            "employee_id": row[1],
            "name": row[2],
            "email": row[3]
        }
    return None

def clear_session():
    """Clear all sessions from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions")
    conn.commit()
    conn.close()

def is_logged_in():
    """Check if a session exists in the database."""
    session = load_session()
    return session is not None

def login_fixhr(email, password, notification_key="123456"):
    # Initialize the database
    init_db()

    if is_logged_in():
        session = load_session()
        return {
            "status": "already_logged_in",
            "message": f"Already logged in as {session.get('name')}",
            "data": session,
        }

    url = "https://dev.fixhr.app/api/auth/login"
    # url = "http://127.0.0.1:8000/api/auth/login"
    payload = {
        "email": email,
        "password": password,
        "notification_key": notification_key,
    }

    try:
        print("🔐 Attempting login with:", email)
        response = requests.post(url, data=payload)
        print("🔐 Login response status:", response.status_code)

        data = response.json()
        if response.status_code == 200 and data.get("success"):
            user = data["data"]["user"]
            token = data["data"]["token"]
            session_data = {
                "token": token,
                "employee_id": user.get("emp_id"),
                "name": user.get("name", "User"),
                "email": user.get("email"),
            }
            save_session(session_data)
            return {"status": "success", "data": session_data}
        return {"status": "fail", "message": data.get("message", "Login failed")}
    except Exception as e:
        return {"status": "fail", "message": str(e)}