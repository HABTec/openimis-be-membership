# db_helper.py
import sqlite3
import time
from pathlib import Path
import json

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
        payment_transactions_query = """
        CREATE TABLE IF NOT EXISTS payment_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            family_id INTEGER,      -- Foreign key to family table
            paypal_transaction_id TEXT UNIQUE,  -- PayPal transaction ID
            amount REAL,            -- Payment amount
            status TEXT,            -- Payment status
            validity_to TIMESTAMP NULL,  -- Validity date (initially NULL)
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        firebase_tokens_query = """
        CREATE TABLE IF NOT EXISTS firebase_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,  -- Foreign key to User table
            fcm_token TEXT UNIQUE,  -- Firebase Cloud Messaging token
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """                
        self.conn.execute(query)
        self.conn.execute(payment_transactions_query)
        self.conn.execute(firebase_tokens_query)
        self.conn.commit()

    def insert_fcm_token(self, user_id, fcm_token):
        """Insert or replace the Firebase token for a user."""
        query = """
        INSERT OR REPLACE INTO firebase_tokens (user_id, fcm_token)
        VALUES (?, ?);
        """
        self.conn.execute(query, (user_id, fcm_token))
        self.conn.commit()

    def get_fcm_token_by_user_id(self, user_id):
        """Retrieve Firebase token by user ID."""
        query = "SELECT fcm_token FROM firebase_tokens WHERE user_id = ?"
        cursor = self.conn.execute(query, (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None  # Return token if found, else None

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


    def insert_payment_transaction(self, family_id, paypal_transaction_id, payment_json):
        """Insert a new payment transaction with full JSON."""
        query = """
        INSERT INTO payment_transactions (family_id, paypal_transaction_id, payment_json)
        VALUES (?, ?, ?);
        """
        self.conn.execute(query, (family_id, paypal_transaction_id, json.dumps(payment_json)))
        self.conn.commit()


    def update_validity_to(self, transaction_id, validity_date):
        """Update the validity_to column for a specific transaction."""
        query = """
        UPDATE payment_transactions
        SET validity_to = ?
        WHERE id = ?;
        """
        self.conn.execute(query, (validity_date, transaction_id))
        self.conn.commit()

    def get_payment_by_transaction_id(self, paypal_transaction_id):
        """Retrieve payment transaction by PayPal transaction ID."""
        query = """
        SELECT * FROM payment_transactions WHERE paypal_transaction_id = ?;
        """
        cursor = self.conn.execute(query, (paypal_transaction_id,))
        return cursor.fetchone()

    def close(self):
        """Close the database connection."""
        self.conn.close()
