# db_helper.py
import sqlite3
import time
from pathlib import Path

DB_PATH = "db.sqlite3"  # Path to SQLite database in root folder

class SQLiteHelper:
    def __init__(self):
        """Initialize the SQLite database and create the table if not exists."""
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.create_table()

    def create_table(self):
        """Create membership_insuree table if it doesn't exist."""
        query = """
        CREATE TABLE IF NOT EXISTS membership_insuree (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            insuree_id INTEGER,  -- Foreign key to Insuree table (main DB)
            phone TEXT UNIQUE,   -- Phone number (must be unique)
            otp_code TEXT,       -- OTP code for validation
            user_id INTEGER NULL,
            otp_expiry INTEGER,  -- Unix timestamp for OTP expiration
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        self.conn.execute(query)
        self.conn.commit()

    def insert_user(self, insuree_id, phone, otp_code):
        """Insert or replace a user with OTP into the table."""
        otp_expiry = int(time.time()) + 300  # OTP valid for 5 minutes
        query = """
        INSERT OR REPLACE INTO membership_insuree (insuree_id, phone, otp_code, otp_expiry)
        VALUES (?, ?, ?, ?);
        """
        self.conn.execute(query, (insuree_id, phone, otp_code, otp_expiry))
        self.conn.commit()

    def get_user_by_phone(self, phone):
        """Retrieve user by phone number."""
        query = "SELECT * FROM membership_insuree WHERE phone = ?"
        
        cursor = self.conn.execute(query, (phone,))
        return cursor.fetchone()

    def delete_user(self, phone):
        """Delete user by phone number."""
        query = "DELETE FROM membership_insuree WHERE phone = ?"
        self.conn.execute(query, (phone,))
        self.conn.commit()


    def update_user_id_by_phone(self, phone, user_id):
        """Update the user_id for the given phone number."""
        query = """
        UPDATE membership_insuree
        SET user_id = ?
        WHERE phone = ?;
        """
        self.conn.execute(query, (user_id, phone))
        self.conn.commit()

    def is_insuree(self, user_id):
        """Check if a user with the given user_id is in the membership_insuree table."""
        query = "SELECT 1 FROM membership_insuree WHERE user_id = ? LIMIT 1"
        cursor = self.conn.execute(query, (user_id,))
        result = cursor.fetchone()  # Fetch the result once
        print("result", result)  # Debugging print to show the result
        return result is not None  # Return True if result exists, else False


    def get_insuree_id_by_user_id(self, user_id):
        """Retrieve insuree_id from membership_insuree table using user_id."""
        query = "SELECT insuree_id FROM membership_insuree WHERE user_id = ? LIMIT 1"
        cursor = self.conn.execute(query, (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None  # Return insuree_id if found, else None

    def update_otp(self, user_id, new_otp):
        """Update the OTP for a specific user."""
        self.conn.execute("UPDATE membership_insuree SET otp_code = ? WHERE id = ?", (new_otp, user_id))
        self.conn.commit()

    def close(self):
        """Close the database connection."""
        self.conn.close()
