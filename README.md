<div align="center">
  <img src="https://img.icons8.com/color/96/000000/heart-health.png" alt="Ease Health Logo" width="80" height="80">

  # 🏥 Ease Health: Integrated Patient Care Management System (IPCMS)
  
  **A next-generation, AI-powered healthcare management platform built for modern clinics.**

  [![Python](https://img.shields.io/badge/Python-3.11+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
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
- **Secure Authentication:** Passwords are encrypted and hashed using `bcrypt`.
- **Session Management:** Secure, persistent sessions using Starlette SessionMiddleware.

### 🤖 2. AI-Powered Smart Booking (Groq + LLaMA 3)
- **Natural Language Appointments:** Patients can book appointments by simply typing what they need.
- **Strict Tool Usage:** The LLM leverages safe Python method bindings (`@tool`) to interact with the database instead of executing raw SQL.

### 📅 3. Interactive Healthcare Scheduling
- **Dashboard Interfaces:** Efficient and minimal dashboards built with HTML/CSS.
- **Direct Booking:** Patients can manage appointments directly from their dashboards.

### 🎨 4. Premium "Ease Health" Design System
- **Bioluminescent Aesthetic:** Sage Mist (`#b1dbb8`), Forest Ink (`#0f3e17`), and Slate Hush (`#b6ced5`).
- **Google Fonts Integration:** Utilizes modern typography (Cormorant Garamond and Inter) for maximum legibility and elegance.

---

## 🛠️ Technology Stack

| Category | Technology |
|---|---|
| **Frontend** | HTML5, Vanilla CSS, Jinja2 Templates, Vanilla JavaScript |
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com/) |
| **Database** | [MySQL](https://www.mysql.com/) (Hosted on [TiDB Cloud](https://en.pingcap.com/tidb-cloud/)) |
| **Database Driver** | `pymysql` (Pure Python MySQL client) |
| **AI Integration** | [Groq API](https://groq.com/) (LLaMA 3), `langchain-groq` |
| **Authentication** | `bcrypt`, `itsdangerous` |

---

## 🚀 Getting Started

### 1. Prerequisites
Ensure you have Python 3.11+ installed.

### 2. Clone & Install
```bash
git clone <repository-url>
cd Springboard
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory:
```env
# TiDB Cloud MySQL Connection
DB_HOST=gateway01.ap-northeast-1.prod.aws.tidbcloud.com
DB_USER=your_username.root
DB_PASSWORD=your_password
DB_NAME=test_db
DB_PORT=4000

# Groq API Key
GROQ_API_KEY=gsk_your_api_key_here
```

### 4. Database Initialization
```bash
python scripts/seed.py
```

### 5. Launch the Application
Start the Uvicorn server to run the FastAPI app:
```bash
python -m uvicorn app.main:app
```
Visit `http://localhost:8000` in your web browser.

---

## 👥 Default Test Accounts
After running `seed.py`, you can log in with:

| Role | Email | Password |
|---|---|---|
| **Admin** | `admin@ease.health` | `Admin@1234` |
| **Doctor** | `dr.sharma@ease.health` | `Doctor@123` |
| **Patient** | `rahul.mehta@email.com` | `Patient@123` |

---

<div align="center">
  <i>Developed for the Infosys Springboard Internship Program.</i><br>
  <b>Building the future of patient care.</b>
</div>
