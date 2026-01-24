from flask import Flask, render_template, request, redirect, url_for, session, flash
import boto3
import uuid
from datetime import datetime
from botocore.exceptions import ClientError

app = Flask(__name__)
app.secret_key = "secure_hospital_key"

# AWS REGION
REGION = "us-east-1"

# AWS SERVICES
dynamodb = boto3.resource("dynamodb", region_name=REGION)
sns = boto3.client("sns", region_name=REGION)

# DYNAMODB TABLES
patients_table = dynamodb.Table("Patients")
admins_table = dynamodb.Table("Admins")
doctors_table = dynamodb.Table("Doctors")
appointments_table = dynamodb.Table("Appointments")
contacts_table = dynamodb.Table("Contacts")

# SNS TOPIC ARN
SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:XXXXXXXXXXX:hospital_notifications"

# SEND NOTIFICATION 
def send_notification(subject, message):
    try:
        sns.publish(TopicArn=SNS_TOPIC_ARN, Subject=subject, Message=message)
    except ClientError as e:
        print("SNS Error:", e)

# HOME 
@app.route("/")
def index():
    session.clear()
    return render_template("index.html")

# ABOUT 
@app.route("/about")
def about():
    return render_template("about.html")

# REGISTER PATIENT 
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        data = request.form
        email = data["email"]

        # Check existing patient
        existing = patients_table.get_item(Key={"email": email})
        if "Item" in existing:
            flash("Patient already registered!")
            return redirect(url_for("login"))

        patient = {
            "email": email,
            "name": data["name"],
            "password": data["password"],
            "dob": data["dob"],
            "blood": data["blood"],
            "allergies": data["allergies"],
            "diseases": data["diseases"]
        }

        patients_table.put_item(Item=patient)

        send_notification("New Patient Registered", f"{email} registered.")

        flash("Registration successful! Login now.")
        return redirect(url_for("login"))

    return render_template("register.html")

# LOGIN PATIENT
@app.route("/login", methods=["GET", "POST"])
def login():
    show_register = False

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        response = patients_table.get_item(Key={"email": email})

        if "Item" not in response:
            flash("User not registered!")
            show_register = True
            return render_template("login.html", show_register=show_register)

        user = response["Item"]

        if user["password"] == password:
            session["patient_email"] = email
            return redirect(url_for("patient_dashboard"))

        flash("Invalid password!")

    return render_template("login.html", show_register=show_register)

# PATIENT DASHBOARD
@app.route("/patient/dashboard")
def patient_dashboard():
    if "patient_email" not in session:
        return redirect(url_for("login"))

    email = session["patient_email"]

    # Load doctors
    doctors = doctors_table.scan().get("Items", [])

    # Load appointments
    appts = appointments_table.scan().get("Items", [])
    my_appts = [a for a in appts if a["patient_email"] == email]

    return render_template("appointments.html", doctors=doctors, appointments=my_appts)

# BOOK APPOINTMENT
@app.route("/book-appointment", methods=["POST"])
def book_appointment():
    if "patient_email" not in session:
        return redirect(url_for("login"))

    appt_id = str(uuid.uuid4())
    data = request.form

    appointment = {
        "appointment_id": appt_id,
        "patient_email": session["patient_email"],
        "doctor": data["doctor"],
        "date": data["date"],
        "time": data["time"],
        "status": "Booked",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    appointments_table.put_item(Item=appointment)

    send_notification(
        "Appointment Booked",
        f"Appointment booked with {data['doctor']} on {data['date']}"
    )

    flash("Appointment booked successfully!")
    return redirect(url_for("patient_dashboard"))

# LOGOUT 
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# DOCTORS PAGE
@app.route("/doctors")
def doctors():
    doctors = doctors_table.scan().get("Items", [])
    return render_template("doctors.html", doctors=doctors)

# ADMIN LOGIN 
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        res = admins_table.get_item(Key={"username": username})

        if "Item" in res and res["Item"]["password"] == password:
            session["admin"] = username
            return redirect(url_for("admin_dashboard"))

        flash("Invalid Admin Login")

    return render_template("admin_login.html")

# ADMIN DASHBOARD 
@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    patients = patients_table.scan().get("Items", [])
    doctors = doctors_table.scan().get("Items", [])
    appointments = appointments_table.scan().get("Items", [])

    return render_template("admin_dashboard.html",
        patients=patients,
        doctors=doctors,
        appointments=appointments
    )

# ADD DOCTOR
@app.route("/admin/add-doctor", methods=["GET", "POST"])
def add_doctor():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        doctor = {
            "doctor_id": str(uuid.uuid4()),
            "name": request.form["name"],
            "specialty": request.form["specialty"],
            "experience": request.form["experience"]
        }

        doctors_table.put_item(Item=doctor)
        send_notification("New Doctor Added", doctor["name"])

        return redirect(url_for("admin_dashboard"))

    return render_template("add_doctor.html")

# CONTACT
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        msg = {
            "message_id": str(uuid.uuid4()),
            "name": request.form["name"],
            "email": request.form["email"],
            "message": request.form["message"]
        }

        contacts_table.put_item(Item=msg)
        flash("Message sent!")

    return render_template("contact.html")

# RUN
if __name__ == "__main__":
    app.run(debug=True)
