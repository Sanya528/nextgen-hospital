# Project Structure

NEXTGEN_HOSPITAL/<br/>
│<br/>
├── static/<br/>
│   ├── css/<br/>
│   ├── images/<br/>
│   └── js/<br/>
│<br/>
├── templates/<br/>
│   ├── 404.html<br/>
│   ├── 500.html<br/>
│   ├── about.html<br/>
│   ├── add_doctor.html<br/>
│   ├── admin_dashboard.html<br/>
│   ├── appointments.html<br/>
│   ├── base.html<br/>
│   ├── contact.html<br/>
│   ├── doctor_details.html<br/>
│   ├── doctors.html<br/>
│   ├── health_tips.html<br/>
│   ├── index.html<br/>
│   ├── login.html<br/>
│   ├── profile.html<br/>
│   └── register.html<br/>
│<br/>
├── app.py              # Local version<br/>
├── app_aws.py          # AWS version<br/>
├── requirements.txt<br/>
├── requirements_aws.txt<br/>
└── README.md<br/>

---

# Features

## Patient Features

Register & Login

View profile

Book & cancel appointments

View appointment history

## Doctor Features

List doctors

View doctor details

## Admin Features

Admin login

Add, edit, delete doctors

View patients, appointments, and contact messages

## Contact System

Users can send inquiries via contact form

## Health Tips

Random daily health tips displayed on homepage

---

# Admin Login Credentials (Default)

Email: admin@hospital.com</br>
Password: admin123

---

# Architecture</br>
The NEXTGEN Hospital application is built using a cloud-ready, AWS-hosted architecture, designed for scalability, persistence, and secure access.</br>
## Frontend</br>
HTML, CSS, JavaScript</br>
Rendered using Flask templates</br>
## Backend</br>
Python Flask web application</br>
Handles authentication, appointments, doctor management, and admin operations</br>
## Database</br>
Amazon DynamoDB (NoSQL)</br>
Stores persistent data for:</br>
Patients</br>
Doctors</br>
Appointments</br>
Contact Messages</br>
## Hosting</br>
Amazon EC2 runs the Flask application server</br>
## Notifications (Optional / Extendable)</br>
Amazon SNS for email or system alerts</br>
## Security</br>
AWS IAM for secure permissions and controlled AWS resource access</br>
Password hashing using Werkzeug Security</br>

--- 

# Tech Stack

Language: Python 3.x</br>
Web Framework: Flask</br>
Cloud Provider: Amazon Web Services (AWS)</br>
AWS Services Used: EC2, DynamoDB, SNS, IAM</br>
Frontend: HTML5, CSS3, JavaScript</br>
Security: Werkzeug Password Hashing</br>
