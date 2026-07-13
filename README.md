<div align="center">
  <img src="assets/ease_logo.png" alt="IPCMS Logo" width="120" style="border-radius: 14px; margin-bottom: 20px;" />
  <h1 align="center">Integrated Patient Care Management System (IPCMS)</h1>
  <p align="center">
    <strong>A next-generation healthcare platform built for the Infosys Springboard Virtual Internship 7.0.</strong>
  </p>
  
  <p align="center">
    <a href="#features"><img src="https://img.shields.io/badge/Features-Explore-0f3e17?style=for-the-badge" alt="Features" /></a>
    <a href="#installation"><img src="https://img.shields.io/badge/Install-Guide-b1dbb8?style=for-the-badge&labelColor=0f3e17" alt="Install" /></a>
    <a href="#tech-stack"><img src="https://img.shields.io/badge/Tech-Stack-e1f4df?style=for-the-badge&labelColor=0f3e17&color=222" alt="Stack" /></a>
  </p>
</div>

---

## 🌟 Overview

IPCMS is a full-stack, AI-powered healthcare management dashboard. Designed with a premium **"botanical greenhouse"** aesthetic, it breaks away from traditional, clunky medical software to provide a serene, highly usable interface for administrators, doctors, and patients alike.

<br>

## ✨ The Entire Feature Set

### 🔐 Strict Role-Based Access Control (RBAC)
The system adapts intelligently based on who logs in:
- **👑 System Administrators**: Complete system oversight. Access to high-level analytics, patient records, and exclusive ability to create and credential new doctor accounts.
- **🩺 Physicians**: Dedicated portal to view daily schedules, manage their availability, record post-visit clinical notes, and update patient health conditions securely.
- **🧑‍⚕️ Patients**: Personal health portal. Ability to self-register, view medical history, book appointments, and interact with the AI assistant.

### 🤖 Profile-Aware AI Clinical Assistant
Powered by Langchain and the Groq LLM (Llama 3.1), the AI assistant is fully contextual:
- **Intelligent Context**: It knows your name, your diagnosed health conditions, and your upcoming appointments.
- **Auto-Booking Engine**: Tell the AI, *"I need to see a cardiologist next week"*, and it will locate an available specialist and **automatically write the appointment to the database**.

### 📊 Live Interactive Analytics
No static images here. The dashboard features **7 dynamic Plotly charts** integrated seamlessly into the custom UI:
- Donut charts for specialty distribution
- Area charts for appointment volume over time
- Horizontal bar charts for doctor workloads
- Treemaps for patient health condition distribution

### 📅 Advanced Scheduling
- **Monthly Interactive Calendar**: A full `streamlit-calendar` implementation allowing users to visualize their schedules visually.
- **Smart Booking Workflow**: Patients select a specialty → view available doctors → select a date & time. The system prevents double-booking.

### 🛡️ Enterprise-Grade Security
- **Remote MySQL Database**: Hosted on TiDB Cloud Serverless with full SSL encryption.
- **Bcrypt Hashing**: Passwords are never stored in plaintext.
- **Strict Password Policies**: Enforcement of uppercase, numbers, special characters, and minimum length requirements on all registrations.

<br>

## 🛠️ Tech Stack

<div align="center">
  <table>
    <tr>
      <td align="center"><b>Frontend</b></td>
      <td align="center">Streamlit, Custom CSS Injection, HTML/JS Components</td>
    </tr>
    <tr>
      <td align="center"><b>Backend</b></td>
      <td align="center">Python 3.12</td>
    </tr>
    <tr>
      <td align="center"><b>Database</b></td>
      <td align="center">TiDB Cloud Serverless (MySQL), `pymysql`</td>
    </tr>
    <tr>
      <td align="center"><b>AI & LLM</b></td>
      <td align="center">Langchain, Groq API</td>
    </tr>
    <tr>
      <td align="center"><b>Visualizations</b></td>
      <td align="center">Plotly, Streamlit-Calendar</td>
    </tr>
  </table>
</div>

<br>

## 🚀 Installation & Setup

Want to run IPCMS locally? Follow these steps:

### 1. Clone & Install
```bash
# Clone the repository
git clone https://github.com/your-username/Integrated-Patient-Care-Management-System.git
cd Integrated-Patient-Care-Management-System

# Create a virtual environment & activate it
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` (or create a new `.env` file) and add your database and API credentials. See the [API & Database Setup Guide](CONTEXT/API_KEY_GUIDE.md) for detailed instructions on getting free TiDB and Groq accounts.
```env
GROQ_API_KEY=your_groq_key
DB_HOST=your_tidb_host
DB_PORT=4000
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=ipcms
```

### 3. Initialize the Database
Run the seed script to automatically create the tables and inject 15+ rows of mock data (doctors, patients, appointments).
```bash
python seed.py
```

### 4. Launch the App
```bash
streamlit run main.py
```
> **Demo Login:** `admin@ease.health` / `Admin@1234`

<br>

## 🎨 Design System

This project strictly adheres to the **"Ease Health"** design system. You can view the full design guidelines, color palette, and typography rules in the [Design Documentation](CONTEXT/DESIGN.md).

<div align="center">
  <br>
  <i>Developed for Infosys Springboard Virtual Internship 7.0</i>
</div>
