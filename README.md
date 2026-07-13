<div align="center">
  <img src="https://img.icons8.com/color/96/000000/heart-health.png" alt="Ease Health Logo" width="80" height="80">

  # 🏥 Ease Health: Integrated Patient Care Management System (IPCMS)
  
  **A next-generation, AI-powered healthcare management platform built for modern clinics.**

  [![Python](https://img.shields.io/badge/Python-3.11+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B.svg?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io/)
  [![MySQL](https://img.shields.io/badge/MySQL-4479A1.svg?style=for-the-badge&logo=mysql&logoColor=white)](https://www.mysql.com/)
  [![TiDB](https://img.shields.io/badge/TiDB-Cloud-313262.svg?style=for-the-badge&logo=tidb&logoColor=white)](https://tidbcloud.com/)
  [![Groq](https://img.shields.io/badge/Groq-AI_Powered-f55036.svg?style=for-the-badge&logo=groq&logoColor=white)](https://groq.com/)
  [![Infosys](https://img.shields.io/badge/Infosys-Springboard-007CC3.svg?style=for-the-badge)](#)
</div>

---

## 🌟 Overview

The **Integrated Patient Care Management System (IPCMS)**, branded as **Ease Health**, is a full-stack, AI-integrated web application designed to streamline clinic operations. It provides dedicated portals for **Patients, Doctors, and Administrators**, ensuring a seamless healthcare experience from booking to consultation.

Built with a stunning, custom-designed **Bioluminescent UI**, it rejects the sterile look of traditional medical software in favor of a modern, engaging, and premium aesthetic.

---

## ✨ Comprehensive Feature Set

### 🔐 1. Role-Based Access Control & Security
- **Multi-Tier Portals:** Distinct dashboards for **Admins**, **Doctors**, and **Patients**.
- **Secure Authentication:** Passwords are encrypted and hashed using `bcrypt` (minimum 8 chars, requires uppercase, special character, and number).
- **Session Management:** Secure, persistent sessions across the application using Streamlit session state.
- **Auto-Login:** Patients are automatically logged in upon successful registration.
- **Password Management:** Every user role has the ability to securely change their password.

### 🤖 2. AI-Powered Smart Booking (Groq + LLaMA 3)
- **Natural Language Appointments:** Patients can book appointments by simply typing what they need (e.g., *"I have a headache, need a doctor on Friday"*).
- **Intelligent Routing:** The AI analyzes the symptoms, finds the appropriate specialist, checks their availability, and schedules the appointment automatically.
- **Strict JSON Schema:** The LLM strictly outputs a pre-defined JSON format to ensure flawless database integration without hallucinations.

### 📅 3. Interactive Healthcare Scheduling
- **Full Monthly Calendar:** A dynamic, color-coded calendar view built with `streamlit-calendar`.
- **Real-Time Availability:** Doctors' schedules are displayed with precise timings (e.g., *Mon-Fri, 9 AM to 5 PM*).
- **Direct Booking:** Patients can click directly on calendar dates to initiate bookings.
- **Status Tracking:** Appointments track statuses (*Scheduled, Completed, Cancelled*) with distinct visual indicators.

### 📊 4. Advanced Analytics & Dashboards
- **Admin Command Center:** Real-time metrics on total patients, doctors, and system-wide appointments.
- **Interactive Visualizations:** Rich, interactive charts built with `Plotly` (e.g., Appointments by Speciality, Patient Demographics).
- **Doctor Workspaces:** Doctors can view their daily schedule, manage patient records, and update appointment statuses.
- **Patient Hub:** Patients can track their upcoming visits, medical history, and interact with the AI assistant.

### 🎨 5. Premium "Ease Health" Design System
- **Bioluminescent Aesthetic:** Deep "Forest Ink" dark mode backgrounds (`#0a1118`) contrasting with vibrant "Bioluminescent Mint" accents (`#00f2fe`).
- **Glassmorphism & Micro-animations:** Frosted glass panels, floating pill navigation bars, and subtle hover states.
- **SVG Iconography:** Sharp, scalable SVG icons instead of emojis for a professional, crisp look.
- **Google Fonts Integration:** Utilizes modern typography (Outfit and Inter) for maximum legibility and elegance.

---

## 🛠️ Technology Stack

| Category | Technology |
|---|---|
| **Frontend** | [Streamlit](https://streamlit.io/), HTML/CSS (Custom Injection), [Plotly](https://plotly.com/python/) |
| **Backend Logic** | Python 3.11+ |
| **Database** | [MySQL](https://www.mysql.com/) (Hosted on [TiDB Cloud](https://en.pingcap.com/tidb-cloud/)) |
| **Database Driver** | `pymysql` (Pure Python MySQL client) |
| **AI Integration** | [Groq API](https://groq.com/) (LLaMA 3 70B / 8B models), `langchain-groq` |
| **Authentication** | `bcrypt` (Password Hashing) |

---

## 🚀 Getting Started

### 1. Prerequisites
Ensure you have Python 3.11+ installed.

### 2. Clone & Install
```bash
# Clone the repository
git clone <repository-url>
cd Springboard

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory and add your credentials:
```env
# TiDB Cloud MySQL Connection
DB_HOST=gateway01.ap-northeast-1.prod.aws.tidbcloud.com
DB_USER=your_username.root
DB_PASSWORD=your_password
DB_NAME=test_db
DB_PORT=4000

# Groq API Key for AI Auto-Booking
GROQ_API_KEY=gsk_your_api_key_here
```
*(Refer to `CONTEXT/API_KEY_GUIDE.md` for detailed instructions on obtaining these keys).*

### 4. Database Initialization
Run the seed script to create all necessary tables and populate the database with mock data (Doctors, Patients, and sample Appointments):
```bash
python seed.py
```

### 5. Launch the Application
```bash
streamlit run main.py
```

---

## 👥 Default Test Accounts
After running `seed.py`, you can log in with these credentials to test the system:

| Role | Email | Password |
|---|---|---|
| **Admin** | `admin@ease.health` | `Admin@1234` |
| **Doctor** | `sarah.chen@ease.health` | `Doc@1234` |
| **Patient** | `john.doe@email.com` | `Pat@1234` |

---

<div align="center">
  <i>Developed for the Infosys Springboard Internship Program.</i><br>
  <b>Building the future of patient care.</b>
</div>
