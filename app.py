from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "hospital_secret"

# ---------------- Local Storage ----------------
patients = []
doctors = []
appointments = []
appointment_counter = 1

# Single Admin
admin_email = "admin@hospital.com"
admin_password = generate_password_hash("admin123")

# ---------------- Home ----------------
@app.route("/")
def index():
    return render_template("index.html")

# ---------------- Patient Signup ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        patient = {
            "id": len(patients)+1,
            "name": request.form["name"],
            "email": request.form["email"],
            "password": generate_password_hash(request.form["password"]),
            "dob": request.form["dob"],
            "blood": request.form["blood"],
            "allergies": request.form["allergies"],
            "diseases": request.form["diseases"]
        }
        patients.append(patient)
        flash("Registration successful")
        print("Patients:", patients)
        return redirect(url_for("login"))

    return render_template("signup.html")

# ---------------- Login ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # Admin login
        if email == admin_email and check_password_hash(admin_password, password):
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))

        # Check if patient exists
        patient_found = None
        for p in patients:
            if p["email"] == email:
                patient_found = p
                break

        if not patient_found:
            flash("You are not registered. Please register first.")
            return render_template("login.html", show_register=True)

        # Validate password
        if check_password_hash(patient_found["password"], password):
            session["patient"] = patient_found
            return redirect(url_for("patient_dashboard"))
        else:
            flash("Incorrect password")

    return render_template("login.html", show_register=False)


# ---------------- Patient Dashboard ----------------
@app.route("/patient")
def patient_dashboard():
    if "patient" not in session:
        return redirect(url_for("login"))

    patient_appointments = [a for a in appointments if a["patient_id"] == session["patient"]["id"]]
    return render_template("patient_dashboard.html", doctors=doctors, data=patient_appointments)

# ---------------- Book Appointment ----------------
@app.route("/book", methods=["POST"])
def book():
    global appointment_counter

    if "patient" not in session:
        return redirect(url_for("login"))

    doctor = request.form["doctor"]
    date = request.form["date"]
    time = request.form["time"]

    appointment = {
        "id": appointment_counter,
        "patient_id": session["patient"]["id"],
        "patient_name": session["patient"]["name"],
        "doctor": doctor,
        "date": date,
        "time": time,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    appointments.append(appointment)
    appointment_counter += 1
    flash("Appointment booked successfully")
    print("Appointments:", appointments)

    return redirect(url_for("patient_dashboard"))


# ---------------- Admin Dashboard ----------------
@app.route("/admin")
def admin_dashboard():
    if "admin" not in session:
        return redirect(url_for("login"))

    return render_template("admin_dashboard.html", doctors=doctors, appointments=appointments, patients=patients)

# ---------------- Add Doctor (Admin) ----------------
@app.route("/add_doctor", methods=["GET", "POST"])
def add_doctor():
    if "admin" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        doctor = {
            "name": request.form["name"],
            "department": request.form["department"]
        }
        doctors.append(doctor)
        flash("Doctor added")
        print("Doctors:", doctors)
        return redirect(url_for("admin_dashboard"))

    return render_template("add_doctor.html")

# ---------------- Logout ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# ---------------- Logout ----------------
@app.route("/about")
def about():
    return render_template("about.html")

if __name__ == "__main__":
    app.run(debug=True)

