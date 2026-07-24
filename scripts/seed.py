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
    """Create all required tables. Drops them first for clean updates."""
    print("Dropping existing tables to prevent conflicts...")
    cursor.execute("DROP TABLE IF EXISTS ai_threads")
    cursor.execute("DROP TABLE IF EXISTS appointments")
    cursor.execute("DROP TABLE IF EXISTS patients")
    cursor.execute("DROP TABLE IF EXISTS doctors")
    cursor.execute("DROP TABLE IF EXISTS specialties")
    cursor.execute("DROP TABLE IF EXISTS users")

    print("Creating tables...")

    cursor.execute("""
    CREATE TABLE users (
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
    CREATE TABLE specialties (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        icon TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE doctors (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT UNIQUE NOT NULL,
        specialty_id INT,
        qualification VARCHAR(255),
        experience_years INT,
        availability VARCHAR(100) DEFAULT 'Mon-Fri, 9AM to 5PM',
        bio TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (specialty_id) REFERENCES specialties(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE patients (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT UNIQUE NOT NULL,
        date_of_birth DATE,
        gender ENUM('Male', 'Female', 'Other'),
        blood_group VARCHAR(5),
        health_condition TEXT,
        emergency_contact VARCHAR(20),
        chat_retention_hours INT DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE ai_threads (
        id INT AUTO_INCREMENT PRIMARY KEY,
        thread_id VARCHAR(255) NOT NULL,
        patient_id INT NOT NULL,
        role ENUM('user', 'assistant') NOT NULL,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NULL,
        FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE appointments (
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

    print("All tables created successfully.")


def seed_data(cursor):
    """Populate tables with initial data."""
    import bcrypt

    def hp(password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    print("Seeding data...")

    # --- Specialties ---
    # Store inline SVG definitions instead of emojis
    specialties = [
        ("Cardiology", "Heart and blood vessels", "<svg viewBox='0 0 24 24' width='24' height='24' stroke='#0f3e17' stroke-width='2' fill='none' stroke-linecap='round' stroke-linejoin='round'><path d='M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z'></path></svg>"),
        ("Dermatology", "Skin, hair and nails", "<svg viewBox='0 0 24 24' width='24' height='24' stroke='#0f3e17' stroke-width='2' fill='none' stroke-linecap='round' stroke-linejoin='round'><path d='M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z'></path></svg>"),
        ("General Medicine", "Broad adult care", "<svg viewBox='0 0 24 24' width='24' height='24' stroke='#0f3e17' stroke-width='2' fill='none' stroke-linecap='round' stroke-linejoin='round'><rect x='3' y='3' width='18' height='18' rx='2' ry='2'></rect><line x1='12' y1='8' x2='12' y2='16'></line><line x1='8' y1='12' x2='16' y2='12'></line></svg>"),
        ("Neurology", "Brain and nervous system", "<svg viewBox='0 0 24 24' width='24' height='24' stroke='#0f3e17' stroke-width='2' fill='none' stroke-linecap='round' stroke-linejoin='round'><polyline points='22 12 18 12 15 21 9 3 6 12 2 12'></polyline></svg>"),
        ("Pediatrics", "Care for children", "<svg viewBox='0 0 24 24' width='24' height='24' stroke='#0f3e17' stroke-width='2' fill='none' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='12' r='10'></circle><path d='M8 14s1.5 2 4 2 4-2 4-2'></path><line x1='9' y1='9' x2='9.01' y2='9'></line><line x1='15' y1='9' x2='15.01' y2='9'></line></svg>"),
        ("Pulmonology", "Lungs and breathing", "<svg viewBox='0 0 24 24' width='24' height='24' stroke='#0f3e17' stroke-width='2' fill='none' stroke-linecap='round' stroke-linejoin='round'><path d='M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2'></path></svg>"),
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
    from faker import Faker
    import random
    fake = Faker('en_IN')

    doctors_data = [
        ("dr.sharma@ease.health", "Doctor@123", "Dr. Priya Sharma", "+91-9100000001", 1, "MD Cardiology, AIIMS", 12, "Specializes in interventional cardiology and preventive heart care."),
        ("dr.patel@ease.health", "Doctor@123", "Dr. Ravi Patel", "+91-9100000002", 4, "MD Neurology, CMC Vellore", 8, "Expert in epilepsy management and neurodegenerative disorders."),
        ("dr.gupta@ease.health", "Doctor@123", "Dr. Ananya Gupta", "+91-9100000003", 5, "MD Pediatrics, KEM Mumbai", 15, "Focuses on neonatal care and childhood developmental conditions."),
    ]
    
    # Generate 6 more doctors
    for i in range(6):
        spec_id = random.randint(1, 6)
        exp_years = random.randint(3, 25)
        doctors_data.append((
            fake.unique.email(),
            "Doctor@123",
            "Dr. " + fake.name(),
            fake.phone_number()[:15],
            spec_id,
            fake.job(),
            exp_years,
            fake.text(max_nb_chars=100)
        ))

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
    print(f"  → {len(doctors_data)} Doctors seeded.")

    # --- Patient Users ---
    patients_data = [
        ("rahul.mehta@email.com", "Patient@123", "Rahul Mehta", "+91-9200000001", "1990-05-15", "Male", "B+", "Mild hypertension, under observation", "+91-9200000099"),
        ("sneha.reddy@email.com", "Patient@123", "Sneha Reddy", "+91-9200000002", "1985-11-22", "Female", "O+", "Type 2 Diabetes, controlled with medication", "+91-9200000098"),
        ("amit.kumar@email.com", "Patient@123", "Amit Kumar", "+91-9200000003", "1978-03-08", "Male", "A-", "Post-cardiac stent procedure, regular follow-up", "+91-9200000097"),
        ("priya.nair@email.com", "Patient@123", "Priya Nair", "+91-9200000004", "1995-07-30", "Female", "AB+", "Seasonal allergies, no chronic conditions", "+91-9200000096"),
        ("dev.joshi@email.com", "Patient@123", "Dev Joshi", "+91-9200000005", "2015-01-12", "Male", "O-", "Childhood asthma, under pediatric care", "+91-9200000095"),
    ]
    
    # Generate 15 more patients
    blood_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    genders = ["Male", "Female", "Other"]
    for i in range(15):
        patients_data.append((
            fake.unique.email(),
            "Patient@123",
            fake.name(),
            fake.phone_number()[:15],
            fake.date_of_birth(minimum_age=5, maximum_age=80).isoformat(),
            random.choice(genders),
            random.choice(blood_groups),
            fake.text(max_nb_chars=50),
            fake.phone_number()[:15]
        ))

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
    print(f"  → {len(patients_data)} Patients seeded.")

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
