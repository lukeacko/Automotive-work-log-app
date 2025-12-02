<h1>🛠️ Automotive Work Log App (Firestore)</h1>

A Python desktop application for managing automotive work logs with Firestore. Track jobs, technicians, status, and dates with a simple, user-friendly interface.

🚀 Features

Add, edit, delete work logs

Track:

Job Number

VIN

Technician

Status (Pending / In Progress / Complete)

Description

Date

Filter and search logs by any field

Sort columns directly in the logs table

Export logs to CSV

Manage technicians (add new technicians)

📸 Screenshots

Main Form: 

View Logs:

⚡ Quick Start
1. Clone the repo
git clone https://github.com/yourusername/automotive-work-log-app.git
cd automotive-work-log-app

2. Install dependencies
pip install tk tkcalendar firebase-admin

3. Configure Firebase

Create a Firebase project and enable Firestore

Generate a service account JSON file

Save it as serviceAccount.json in the project folder

4. Run the app
python main_firestore.py

📝 Usage

Add a job: Fill all fields → Save Entry

View logs: Click View Job Logs → filter or sort → Search

Edit a job: Double-click a row or select → Edit Selected

Delete a job: Select a row → Delete Selected

Export CSV: Click Export CSV in logs view

⚙️ Requirements

Python 3.10+

Tkinter

tkcalendar

Firebase Admin SDK

🛠️ Project Structure
/automotive-work-log-app
│
├─ main_firestore.py       # Main application
├─ serviceAccount.json    # Firebase credentials
├─ README.md              # This file
└─ screenshots/           # Screenshots of application

📄 License

MIT License
