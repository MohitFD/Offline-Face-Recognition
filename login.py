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
        INSERT OR REPLACE INTO sessions (
            token,
            employee_id,
            name,
            email,
            business_id,
            business_name,
            branch_id,
            user_id,
            phone,
            emp_code,
            role_name,
            role_id,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["token"],
            data["employee_id"],
            data["name"],
            data["email"],
            data.get("business_id"),
            data.get("business_name"),
            data.get("branch_id"),
            data.get("user_id"),
            data.get("phone"),
            data.get("emp_code"),
            data.get("role_name"),
            data.get("role_id"),
            datetime.utcnow(),
        )
    )
    conn.commit()
    conn.close()

def load_session():
    """Load session data from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            token,
            employee_id,
            name,
            email,
            business_id,
            business_name,
            branch_id,
            user_id,
            phone,
            emp_code,
            role_name,
            role_id
        FROM sessions
        LIMIT 1
        """
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "token": row[0],
            "employee_id": row[1],
            "name": row[2],
            "email": row[3],
            "business_id": row[4],
            "business_name": row[5],
            "branch_id": row[6],
            "user_id": row[7],
            "phone": row[8],
            "emp_code": row[9],
            "role_name": row[10],
            "role_id": row[11],
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

    url = "https://fixhr.app/api/auth/login"
    # url = "https://dev.fixhr.app/api/auth/login"
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
        print("🔐 Login data:", data)
        if response.status_code == 200 and data.get("success"):
            user = data["data"]["user"]
            token = data["data"]["token"]
            role = user.get("role") or {}
            session_data = {
                "token": token,
                "employee_id": user.get("emp_id"),
                "name": user.get("name", "User"),
                "email": user.get("email"),
                "business_id": user.get("business_id"),
                "business_name": user.get("business_name") or user.get("company_name") or user.get("name"),
                "branch_id": user.get("branch_id"),
                "user_id": user.get("user_id"),
                "phone": user.get("phone"),
                "emp_code": user.get("emp_code"),
                "role_name": role.get("role_name"),
                "role_id": role.get("role_id"),
            }
            save_session(session_data)
            return {"status": "success", "data": session_data}
        return {"status": "fail", "message": data.get("message", "Login failed")}
    except Exception as e:
        return {"status": "fail", "message": str(e)}