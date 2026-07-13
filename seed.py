"""
seed.py — Database Initialization & Seed Data
Run once to create all tables and populate with initial data.
Usage: python seed.py
"""

import pymysql
import os
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Get a raw connection (same as db.py but standalone for seeding)."""
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 4000)),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "ipcms"),
        ssl={"ssl": True} if os.getenv("DB_HOST", "localhost") != "localhost" else None,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def create_tables(cursor):
    """Create all required tables."""
    print("Creating tables...")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        role ENUM('admin', 'doctor', 'patient') NOT NULL,
        full_name VARCHAR(255) NOT NULL,
        phone VARCHAR(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS specialties (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        icon VARCHAR(10)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctors (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT UNIQUE NOT NULL,
        specialty_id INT,
        qualification VARCHAR(255),
        experience_years INT,
        availability ENUM('available', 'busy', 'off_duty') DEFAULT 'available',
        bio TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (specialty_id) REFERENCES specialties(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT UNIQUE NOT NULL,
        date_of_birth DATE,
        gender ENUM('Male', 'Female', 'Other'),
        blood_group VARCHAR(5),
        health_condition TEXT,
        emergency_contact VARCHAR(20),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        patient_id INT NOT NULL,
        doctor_id INT NOT NULL,
        appointment_date DATE NOT NULL,
        appointment_time TIME NOT NULL,
        status ENUM('scheduled', 'completed', 'cancelled') DEFAULT 'scheduled',
        reason TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
        FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
    )
    """)

    print("✅ All tables created successfully.")


def seed_data(cursor):
    """Populate tables with initial data."""
    import bcrypt

    def hp(password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Check if data already exists
    cursor.execute("SELECT COUNT(*) as cnt FROM users")
    if cursor.fetchone()['cnt'] > 0:
        print("⚠️  Data already exists. Skipping seed. Drop tables first to re-seed.")
        return

    print("Seeding data...")

    # --- Specialties ---
    specialties = [
        ("Cardiology", "Heart and blood vessels", "❤️"),
        ("Dermatology", "Skin, hair and nails", "🧴"),
        ("General Medicine", "Broad adult care", "➕"),
        ("Neurology", "Brain and nervous system", "🧠"),
        ("Pediatrics", "Care for children", "👶"),
        ("Pulmonology", "Lungs and breathing", "🫁"),
    ]
    for name, desc, icon in specialties:
        cursor.execute(
            "INSERT INTO specialties (name, description, icon) VALUES (%s, %s, %s)",
            (name, desc, icon)
        )
    print("  → Specialties seeded.")

    # --- Admin User ---
    cursor.execute(
        "INSERT INTO users (email, password_hash, role, full_name, phone) VALUES (%s, %s, 'admin', %s, %s)",
        ("admin@ease.health", hp("Admin@1234"), "System Administrator", "+91-9000000000")
    )
    print("  → Admin seeded: admin@ease.health / Admin@1234")

    # --- Doctor Users ---
    doctors_data = [
        ("dr.sharma@ease.health", "Doctor@123", "Dr. Priya Sharma", "+91-9100000001", 1, "MD Cardiology, AIIMS", 12, "Specializes in interventional cardiology and preventive heart care."),
        ("dr.patel@ease.health", "Doctor@123", "Dr. Ravi Patel", "+91-9100000002", 4, "MD Neurology, CMC Vellore", 8, "Expert in epilepsy management and neurodegenerative disorders."),
        ("dr.gupta@ease.health", "Doctor@123", "Dr. Ananya Gupta", "+91-9100000003", 5, "MD Pediatrics, KEM Mumbai", 15, "Focuses on neonatal care and childhood developmental conditions."),
    ]
    for email, pwd, name, phone, spec_id, qual, exp, bio in doctors_data:
        cursor.execute(
            "INSERT INTO users (email, password_hash, role, full_name, phone) VALUES (%s, %s, 'doctor', %s, %s)",
            (email, hp(pwd), name, phone)
        )
        user_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO doctors (user_id, specialty_id, qualification, experience_years, bio) VALUES (%s, %s, %s, %s, %s)",
            (user_id, spec_id, qual, exp, bio)
        )
    print("  → 3 Doctors seeded.")

    # --- Patient Users ---
    patients_data = [
        ("rahul.mehta@email.com", "Patient@123", "Rahul Mehta", "+91-9200000001", "1990-05-15", "Male", "B+", "Mild hypertension, under observation", "+91-9200000099"),
        ("sneha.reddy@email.com", "Patient@123", "Sneha Reddy", "+91-9200000002", "1985-11-22", "Female", "O+", "Type 2 Diabetes, controlled with medication", "+91-9200000098"),
        ("amit.kumar@email.com", "Patient@123", "Amit Kumar", "+91-9200000003", "1978-03-08", "Male", "A-", "Post-cardiac stent procedure, regular follow-up", "+91-9200000097"),
        ("priya.nair@email.com", "Patient@123", "Priya Nair", "+91-9200000004", "1995-07-30", "Female", "AB+", "Seasonal allergies, no chronic conditions", "+91-9200000096"),
        ("dev.joshi@email.com", "Patient@123", "Dev Joshi", "+91-9200000005", "2015-01-12", "Male", "O-", "Childhood asthma, under pediatric care", "+91-9200000095"),
    ]
    patient_ids = []
    for email, pwd, name, phone, dob, gender, blood, condition, emg in patients_data:
        cursor.execute(
            "INSERT INTO users (email, password_hash, role, full_name, phone) VALUES (%s, %s, 'patient', %s, %s)",
            (email, hp(pwd), name, phone)
        )
        user_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO patients (user_id, date_of_birth, gender, blood_group, health_condition, emergency_contact) VALUES (%s, %s, %s, %s, %s, %s)",
            (user_id, dob, gender, blood, condition, emg)
        )
        patient_ids.append(cursor.lastrowid)
    print("  → 5 Patients seeded.")

    # --- Appointments ---
    # Get doctor IDs
    cursor.execute("SELECT id FROM doctors ORDER BY id")
    doctor_ids = [row['id'] for row in cursor.fetchall()]

    appointments_data = [
        (patient_ids[0], doctor_ids[0], "2026-07-15", "10:00:00", "scheduled", "Routine BP checkup"),
        (patient_ids[0], doctor_ids[0], "2026-07-08", "09:30:00", "completed", "Follow-up on hypertension medication"),
        (patient_ids[1], doctor_ids[0], "2026-07-16", "11:00:00", "scheduled", "Cardiac risk assessment for diabetes patient"),
        (patient_ids[2], doctor_ids[0], "2026-07-10", "14:00:00", "completed", "Post-stent follow-up"),
        (patient_ids[2], doctor_ids[0], "2026-07-20", "10:30:00", "scheduled", "Cardiac imaging review"),
        (patient_ids[3], doctor_ids[1], "2026-07-17", "15:00:00", "scheduled", "Migraine evaluation"),
        (patient_ids[4], doctor_ids[2], "2026-07-18", "09:00:00", "scheduled", "Asthma management review"),
        (patient_ids[1], doctor_ids[1], "2026-07-05", "13:00:00", "completed", "Diabetic neuropathy screening"),
    ]
    for pid, did, date, time, status, reason in appointments_data:
        notes = "Patient vitals stable. Continue current medication." if status == "completed" else None
        cursor.execute(
            "INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, status, reason, notes) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (pid, did, date, time, status, reason, notes)
        )
    print("  → 8 Appointments seeded.")

    print("\n✅ All seed data inserted successfully!")


if __name__ == "__main__":
    print("=" * 50)
    print("IPCMS Database Seeder")
    print("=" * 50)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            create_tables(cursor)
            seed_data(cursor)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure your .env file has the correct DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME values.")
    finally:
        conn.close()

    print("\nDone!")
