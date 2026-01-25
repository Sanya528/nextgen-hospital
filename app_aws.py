from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import uuid, random
from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Key

app = Flask(__name__)
app.secret_key = "nextgen_secret"

REGION = "us-east-1"
dynamodb = boto3.resource("dynamodb", region_name=REGION)

patients_table = dynamodb.Table("Patients")
appointments_table = dynamodb.Table("Appointments")
contacts_table = dynamodb.Table("Contacts")
doctors_table = dynamodb.Table("Doctors")

ADMIN_EMAIL = "admin@hospital.com"
ADMIN_PASSWORD = generate_password_hash("admin123")

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

@app.route("/")
def home():
    tips = random.sample(health_tips, min(4, len(health_tips)))
    return render_template("index.html", tips=tips)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        contacts_table.put_item(Item={
            "id": str(uuid.uuid4()),
            "name": request.form["name"],
            "email": request.form["email"],
            "message": request.form["message"],
            "timestamp": datetime.now().isoformat()
        })
        flash("Message sent successfully!")
    return render_template("contact.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]

        existing = patients_table.get_item(Key={"email": email})
        if "Item" in existing:
            flash("Email already registered")
            return redirect(url_for("login"))

        patients_table.put_item(Item={
            "id": str(uuid.uuid4()),
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

@app.route("/login", methods=["GET", "POST"])
def login():
    show_register = False

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # Admin Login
        if email == ADMIN_EMAIL and check_password_hash(ADMIN_PASSWORD, password):
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))

        # Patient Login
        res = patients_table.get_item(Key={"email": email})
        user = res.get("Item")

        if user and check_password_hash(user["password"], password):
            session["patient_email"] = user["email"]
            session["patient_id"] = user["id"]
            return redirect(url_for("profile"))

        flash("Invalid credentials")
        show_register = True

    return render_template("login.html", show_register=show_register)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/doctors")
def doctors():
    res = doctors_table.scan()
    doctors = res.get("Items", [])
    return render_template("doctors.html", doctors=doctors)

@app.route("/doctor/<doctor_id>")
def doctor_details(doctor_id):
    res = doctors_table.get_item(Key={"id": doctor_id})
    doctor = res.get("Item")
    return render_template("doctor_details.html", doctor=doctor)

@app.route("/appointments")
def appointments_page():
    if not is_logged_in():
        return redirect(url_for("login"))

    res = appointments_table.scan()
    my_appts = [a for a in res.get("Items", []) if a["patient_id"] == session["patient_id"]]

    return render_template("appointments.html", doctors=get_doctors(), appointments=my_appts)

@app.route("/book-appointment", methods=["POST"])
def book_appointment():
    if not is_logged_in():
        return redirect(url_for("login"))

    appointments_table.put_item(Item={
        "id": str(uuid.uuid4()),
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
    appointments_table.update_item(
        Key={"id": appt_id},
        UpdateExpression="SET #s = :val",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":val": "Cancelled"}
    )

    flash("Appointment cancelled")
    return redirect(url_for("appointments_page"))

def get_doctors():
    res = doctors_table.scan()
    return res.get("Items", [])

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if not is_logged_in():
        return redirect(url_for("login"))

    patient_id = session.get("patient_id")

    res = patients_table.scan()
    patient = next((p for p in res.get("Items", []) if p["id"] == patient_id), None)

    if patient is None:
        flash("Session expired. Please login again.")
        session.clear()
        return redirect(url_for("login"))

    appts_res = appointments_table.scan()
    my_appts = [a for a in appts_res.get("Items", []) if a["patient_id"] == patient_id]

    if request.method == "POST":
        appointments_table.put_item(Item={
            "id": str(uuid.uuid4()),
            "patient_id": patient_id,
            "patient_email": session["patient_email"],
            "doctor": request.form["doctor"],
            "date": request.form["date"],
            "time": request.form["time"],
            "status": "Booked",
            "timestamp": datetime.now().isoformat()
        })
        flash("Appointment booked successfully!")
        return redirect(url_for("profile"))

    return render_template(
        "profile.html",
        patient=patient,
        appointments=my_appts,
        doctors=get_doctors()
    )

@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect(url_for("login"))

    patients = patients_table.scan().get("Items", [])
    appointments = appointments_table.scan().get("Items", [])
    contacts = contacts_table.scan().get("Items", [])
    doctors = doctors_table.scan().get("Items", [])

    return render_template(
        "admin_dashboard.html",
        doctors=doctors,
        patients=patients,
        appointments=appointments,
        contacts=contacts
    )

@app.route("/admin/add-doctor", methods=["GET", "POST"])
def add_doctor():
    if "admin" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        doctors_table.put_item(Item={
            "id": str(uuid.uuid4()),
            "name": request.form["name"],
            "specialty": request.form["specialty"],
            "experience": int(request.form["experience"]),
            "image": request.form["image"]
        })
        return redirect(url_for("admin_dashboard"))

    return render_template("add_doctor.html")

@app.route("/admin/edit-doctor/<doctor_id>", methods=["GET", "POST"])
def edit_doctor(doctor_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    res = doctors_table.get_item(Key={"id": doctor_id})
    doctor = res.get("Item")

    if request.method == "POST":
        doctors_table.update_item(
            Key={"id": doctor_id},
            UpdateExpression="SET #n=:n, specialty=:s, experience=:e, image=:i",
            ExpressionAttributeNames={"#n": "name"},
            ExpressionAttributeValues={
                ":n": request.form["name"],
                ":s": request.form["specialty"],
                ":e": int(request.form["experience"]),
                ":i": request.form["image"]
            }
        )
        return redirect(url_for("admin_dashboard"))

    return render_template("add_doctor.html", doctor=doctor, edit=True)

@app.route("/admin/delete-doctor/<doctor_id>")
def delete_doctor(doctor_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    doctors_table.delete_item(Key={"id": doctor_id})
    return redirect(url_for("admin_dashboard"))

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def error(e):
    return render_template("500.html"), 500

if __name__ == "__main__":
    app.run(debug=True)
