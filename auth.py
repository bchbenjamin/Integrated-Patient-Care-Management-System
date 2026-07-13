"""
auth.py — Authentication, Password Hashing & Validation
Handles user login, patient registration, and password policy enforcement.
Passwords must contain: uppercase, special character, number, min 8 chars.
"""

import re
try:
    import bcrypt
except ModuleNotFoundError:
    import sys, subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "bcrypt"])
finally:
    import bcrypt
from db import fetch_one, execute_query


def hash_password(plain_password: str) -> str:
    """Hash a password using bcrypt with auto-generated salt."""
    return bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password against policy:
    - Minimum 8 characters
    - At least 1 uppercase letter
    - At least 1 number
    - At least 1 special character (!@#$%^&*()_+-=[]{}|;:',.<>?/`~)
    Returns (is_valid, error_message).
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number."
    if not re.search(r'[!@#$%^&*()\-_+=\[\]{}|;:\'",.<>?/`~]', password):
        return False, "Password must contain at least one special character."
    return True, ""


def login_user(email: str, password: str) -> dict | None:
    """
    Authenticate a user by email and password.
    Returns the user dict (id, email, role, full_name) on success, None on failure.
    """
    user = fetch_one("SELECT * FROM users WHERE email = %s", (email,))
    if user and verify_password(password, user['password_hash']):
        # Don't return the hash to the session
        del user['password_hash']
        return user
    return None


def register_patient(email: str, password: str, full_name: str, phone: str = None,
                     date_of_birth: str = None, gender: str = None, 
                     blood_group: str = None, emergency_contact: str = None) -> tuple[bool, str]:
    """
    Register a new patient. Validates password policy, checks for duplicate email.
    Returns (success, message).
    """
    # Check password policy
    is_valid, msg = validate_password(password)
    if not is_valid:
        return False, msg

    # Check if email already exists
    existing = fetch_one("SELECT id FROM users WHERE email = %s", (email,))
    if existing:
        return False, "An account with this email already exists."

    # Create user record
    hashed = hash_password(password)
    user_id = execute_query(
        "INSERT INTO users (email, password_hash, role, full_name, phone) VALUES (%s, %s, 'patient', %s, %s)",
        (email, hashed, full_name, phone)
    )

    # Create patient profile
    execute_query(
        "INSERT INTO patients (user_id, date_of_birth, gender, blood_group, emergency_contact) VALUES (%s, %s, %s, %s, %s)",
        (user_id, date_of_birth, gender, blood_group, emergency_contact)
    )

    return True, "Registration successful! You can now log in."


def create_doctor(email: str, password: str, full_name: str, phone: str = None,
                  specialty_id: int = None, qualification: str = None,
                  experience_years: int = None, bio: str = None) -> tuple[bool, str]:
    """
    Create a new doctor account. Admin-only operation.
    Returns (success, message).
    """
    is_valid, msg = validate_password(password)
    if not is_valid:
        return False, msg

    existing = fetch_one("SELECT id FROM users WHERE email = %s", (email,))
    if existing:
        return False, "An account with this email already exists."

    hashed = hash_password(password)
    user_id = execute_query(
        "INSERT INTO users (email, password_hash, role, full_name, phone) VALUES (%s, %s, 'doctor', %s, %s)",
        (email, hashed, full_name, phone)
    )

    execute_query(
        "INSERT INTO doctors (user_id, specialty_id, qualification, experience_years, bio) VALUES (%s, %s, %s, %s, %s)",
        (user_id, specialty_id, qualification, experience_years, bio)
    )

    return True, f"Doctor '{full_name}' created successfully."
