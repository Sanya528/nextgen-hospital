from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid
import random

app = Flask(__name__)
app.secret_key = "next_gen_secret"

# ---------------- LOCAL DATABASE ----------------
users = []           # Patients
doctors = []         # Doctors added by admin
appointments = []    # Bookings
contacts = []        # Contact messages

# ---------------- ADMIN LOGIN ----------------
ADMIN_EMAIL = "admin@hospital.com"
ADMIN_PASSWORD = generate_password_hash("admin123")

# ---------------- HEALTH TIPS ----------------
health_tips = [
    {"title": "Stay Hydrated", "content": "Drink at least 8 glasses of water daily."},
    {"title": "Exercise Daily", "content": "30 minutes of activity keeps you fit."},
    {"title": "Healthy Diet", "content": "Eat fruits and vegetables regularly."},
    {"title": "Good Sleep", "content": "Sleep 7-8 hours every night."}
]

# ---------------- COMMON AILMENTS ----------------
common_ailments = {
    "Flu": {"symptoms": "Fever, cold", "remedy": "Rest & fluids"},
    "Headache": {"symptoms": "Pain", "remedy": "Hydration & rest"},
    "Diabetes": {"symptoms": "Fatigue", "remedy": "Consult doctor"}
}

# ---------------- HELPER ----------------
def is_logged_in():
    return "user_email" in session

@app.context_processor
def inject_now():
    return {"now": datetime.now()}

# ---------------- HOME ----------------
@app.route("/")
def home():
    session.clear()  # Auto logout when Home clicked
    
    tips = random.sample(health_tips, min(3, len(health_tips)))
    return render_template("index.html", tips=tips)


# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = {
            "id": str(uuid.uuid4()),
            "name": request.form["name"],
            "email": request.form["email"],
            "password": generate_password_hash(request.form["password"]),
            "dob": request.form["dob"],
            "blood": request.form["blood"],
            "allergies": request.form["allergies"],
            "diseases": request.form["diseases"]
        }
        users.append(user)
        flash("Registration successful")
        return redirect(url_for("login"))

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # Admin login
        if email == ADMIN_EMAIL and check_password_hash(ADMIN_PASSWORD, password):
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))

        # Patient login
        for u in users:
            if u["email"] == email:
                if check_password_hash(u["password"], password):
                    session["user_email"] = u["email"]
                    session["user_id"] = u["id"]
                    return redirect(url_for("profile"))
                else:
                    flash("Incorrect password")
                    return redirect(url_for("login"))

        flash("User not registered")
        return render_template("login.html", show_register=True)

    return render_template("login.html", show_register=False)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out")
    return redirect(url_for("home"))

# ---------------- ABOUT ----------------
@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        contacts.append(request.form.to_dict())
        flash("Message sent successfully!")
        return redirect(url_for("contact"))

    return render_template("contact.html")

# ---------------- DOCTORS ----------------
@app.route("/doctors")
def doctors_page():
    return render_template("doctors.html", doctors=doctors)

# ---------------- DOCTOR DETAILS ----------------
@app.route("/doctor/<doctor_id>")
def doctor_details(doctor_id):
    doc = next((d for d in doctors if d["id"] == doctor_id), None)
    return render_template("doctor_details.html", doctor=doc)

# ---------------- APPOINTMENTS ----------------
@app.route("/appointments")
def appointments_page():
    if not is_logged_in():
        return redirect(url_for("login"))

    user_appts = [a for a in appointments if a["user_id"] == session["user_id"]]
    return render_template("appointments.html", doctors=doctors, appointments=user_appts)

# ---------------- BOOK APPOINTMENT ----------------
@app.route("/book-appointment", methods=["POST"])
def book_appointment():
    appt = {
        "id": str(uuid.uuid4()),
        "user_id": session["user_id"],
        "doctor": request.form["doctor"],
        "date": request.form["date"],
        "time": request.form["time"],
        "status": "Booked"
    }
    appointments.append(appt)
    flash("Appointment booked successfully")
    return redirect(url_for("appointments_page"))

# ---------------- CANCEL APPOINTMENT ----------------
@app.route("/cancel-appointment/<appt_id>")
def cancel_appointment(appt_id):
    for a in appointments:
        if a["id"] == appt_id:
            a["status"] = "Cancelled"
    flash("Appointment cancelled")
    return redirect(url_for("appointments_page"))

# ---------------- HEALTH TIPS ----------------
@app.route("/health-tips")
def health_tips_page():
    return render_template("health_tips.html", tips=health_tips, ailments=common_ailments)

# ---------------- PROFILE ----------------
@app.route("/profile")
def profile():
    user = next((u for u in users if u["id"] == session.get("user_id")), None)
    user_appts = [a for a in appointments if a["user_id"] == session.get("user_id")]
    return render_template("profile.html", user=user, appointments=user_appts)

# ---------------- UPDATE PROFILE ----------------
@app.route("/update-profile", methods=["POST"])
def update_profile():
    for u in users:
        if u["id"] == session["user_id"]:
            u["name"] = request.form["name"]
            u["blood"] = request.form["blood"]
            u["allergies"] = request.form["allergies"]
            u["diseases"] = request.form["diseases"]
    flash("Profile updated")
    return redirect(url_for("profile"))

# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin")
def admin_dashboard():
    if "admin" not in session:
        return redirect(url_for("login"))

    return render_template(
        "admin_dashboard.html",
        users=users,
        doctors=doctors,
        appointments=appointments,
        contacts=contacts
    )

# ---------------- ADD DOCTOR ----------------
@app.route("/add-doctor", methods=["GET", "POST"])
def add_doctor():
    if "admin" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        doc = {
            "id": str(uuid.uuid4()),
            "name": request.form["name"],
            "specialty": request.form["specialty"],
            "experience": request.form["experience"]
        }
        doctors.append(doc)
        flash("Doctor added")
        return redirect(url_for("admin_dashboard"))

    return render_template("add_doctor.html")

# ---------------- ERROR HANDLERS ----------------
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
