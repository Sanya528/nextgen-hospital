from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import uuid, random, os
from datetime import datetime
import boto3

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "nextgen_secret")

# ========================
# AWS CONFIG
# ========================
REGION = os.environ.get("AWS_REGION", "us-east-1")
dynamodb = boto3.resource("dynamodb", region_name=REGION)

patients_table = dynamodb.Table("Patients")
appointments_table = dynamodb.Table("Appointments")
contacts_table = dynamodb.Table("Contacts")
doctors_table = dynamodb.Table("Doctors")

# ========================
# ADMIN LOGIN
# ========================
ADMIN_EMAIL = "admin@hospital.com"
ADMIN_PASSWORD = "admin123"

# ========================
# HEALTH TIPS
# ========================
health_tips = [
    {"title": "Stay Hydrated", "content": "Drink at least 7–8 glasses of water daily."},
    {"title": "Eat Balanced Meals", "content": "Include fruits, vegetables, and whole grains."},
    {"title": "Exercise Regularly", "content": "At least 30 minutes of activity daily."},
    {"title": "Get Enough Sleep", "content": "Aim for 7–9 hours of sleep."},
    {"title": "Manage Stress", "content": "Practice meditation or relaxation."},
    {"title": "Limit Junk Food", "content": "Avoid excess sugar and processed foods."},
    {"title": "Maintain Hygiene", "content": "Wash hands regularly to prevent infections."},
    {"title": "Regular Checkups", "content": "Early detection saves lives."},
]

def is_logged_in():
    return "patient_email" in session

# ========================
# HOME
# ========================
@app.route("/")
def home():
    tips = random.sample(health_tips, min(4, len(health_tips)))
    return render_template("index.html", tips=tips)

@app.route("/about")
def about():
    return render_template("about.html")

# ========================
# CONTACT
# ========================
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        contacts_table.put_item(Item={
            "contact_id": str(uuid.uuid4()),
            "name": request.form["name"],
            "email": request.form["email"],
            "message": request.form["message"],
            "timestamp": datetime.now().isoformat()
        })
        flash("Message sent successfully!")
    return render_template("contact.html")

# ========================
# REGISTER
# ========================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]

        existing = patients_table.scan().get("Items", [])
        for p in existing:
            if p["email"] == email:
                flash("Email already registered")
                return redirect(url_for("login"))

        patients_table.put_item(Item={
            "patient_id": str(uuid.uuid4()),
            "name": request.form["name"],
            "email": email,
            "password": generate_password_hash(request.form["password"]),
            "dob": request.form["dob"],
            "blood": request.form["blood"],
            "allergies": request.form["allergies"],
            "diseases": request.form["diseases"]
        })

        flash("Registration successful. Login now.")
        return redirect(url_for("login"))

    return render_template("register.html")

# ========================
# LOGIN
# ========================
@app.route("/login", methods=["GET", "POST"])
def login():
    show_register = False

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # ADMIN LOGIN
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))

        # PATIENT LOGIN
        try:
            patients = patients_table.scan().get("Items", [])
            for p in patients:
                if p.get("email") == email and check_password_hash(p.get("password"), password):
                    session["patient_email"] = p.get("email")
                    session["patient_id"] = p.get("patient_id")
                    return redirect(url_for("profile"))
        except:
            pass

        flash("Invalid credentials")
        show_register = True

    return render_template("login.html", show_register=show_register)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# ========================
# DOCTORS
# ========================
@app.route("/doctors")
def doctors():
    doctors = doctors_table.scan().get("Items", [])
    return render_template("doctors.html", doctors=doctors)

@app.route("/doctor/<doctor_id>")
def doctor_details(doctor_id):
    res = doctors_table.get_item(Key={"doctor_id": doctor_id})
    doctor = res.get("Item")

    if not doctor:
        return redirect(url_for("doctors"))

    return render_template("doctor_details.html", doctor=doctor)

# ========================
# APPOINTMENTS
# ========================
@app.route("/appointments")
def appointments_page():
    if not is_logged_in():
        return redirect(url_for("login"))

    appts = appointments_table.scan().get("Items", [])
    my_appts = [a for a in appts if a["patient_id"] == session["patient_id"]]

    doctors = doctors_table.scan().get("Items", [])
    return render_template("appointments.html", doctors=doctors, appointments=my_appts)

@app.route("/book-appointment", methods=["POST"])
def book_appointment():
    if not is_logged_in():
        return redirect(url_for("login"))

    appointments_table.put_item(Item={
        "appointment_id": str(uuid.uuid4()),
        "patient_id": session["patient_id"],
        "patient_email": session["patient_email"],
        "doctor": request.form["doctor"],
        "date": request.form["date"],
        "time": request.form["time"],
        "status": "Booked",
        "timestamp": datetime.now().isoformat()
    })

    flash("Appointment booked successfully")
    return redirect(url_for("appointments_page"))

@app.route("/cancel/<appt_id>")
def cancel(appt_id):
    res = appointments_table.get_item(Key={"appointment_id": appt_id})
    appt = res.get("Item")

    if appt:
        appt["status"] = "Cancelled"
        appointments_table.put_item(Item=appt)

    flash("Appointment cancelled")
    return redirect(url_for("appointments_page"))

# ========================
# PROFILE
# ========================
@app.route("/profile")
def profile():
    if not is_logged_in():
        return redirect(url_for("login"))

    pid = session.get("patient_id")

    patients = patients_table.scan().get("Items", [])
    patient = next((p for p in patients if p["patient_id"] == pid), None)

    if not patient:
        session.clear()
        return redirect(url_for("login"))

    appts = appointments_table.scan().get("Items", [])
    my_appts = [a for a in appts if a["patient_id"] == pid]

    doctors = doctors_table.scan().get("Items", [])

    return render_template("profile.html", patient=patient, appointments=my_appts, doctors=doctors)

# ========================
# ADMIN DASHBOARD
# ========================
@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect(url_for("login"))

    doctors = doctors_table.scan().get("Items", [])
    patients = patients_table.scan().get("Items", [])
    appointments = appointments_table.scan().get("Items", [])
    contacts = contacts_table.scan().get("Items", [])

    return render_template("admin_dashboard.html",
        doctors=doctors,
        patients=patients,
        appointments=appointments,
        contacts=contacts
    )

# ========================
# ADMIN ADD DOCTOR (NO IMAGE)
# ========================
@app.route("/admin/add-doctor", methods=["GET", "POST"])
def add_doctor():
    if "admin" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        doctors_table.put_item(Item={
            "doctor_id": str(uuid.uuid4()),
            "name": request.form["name"],
            "specialty": request.form["specialty"],
            "experience": request.form["experience"]
        })
        return redirect(url_for("admin_dashboard"))

    return render_template("add_doctor.html")

# ========================
# RUN
# ========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
