### Project Structure

NEXTGEN_HOSPITAL/
│
├── static/
│   ├── css/
│   ├── images/
│   └── js/
│
├── templates/
│   ├── 404.html
│   ├── 500.html
│   ├── about.html
│   ├── add_doctor.html
│   ├── admin_dashboard.html
│   ├── appointments.html
│   ├── base.html
│   ├── contact.html
│   ├── doctor_details.html
│   ├── doctors.html
│   ├── health_tips.html
│   ├── index.html
│   ├── login.html
│   ├── profile.html
│   └── register.html
│
├── app.py              # Local version (in-memory storage)
├── app_aws.py          # AWS DynamoDB version
├── requirements.txt
├── requirements_aws.txt
└── README.md

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
