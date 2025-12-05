from flask import Flask, render_template, request, redirect, session, url_for

app = Flask(__name__)
app.secret_key = "secret_key_here"

# Lưu tạm (in-memory)
users = {}
treatments = []   # mỗi item: {"id": int, "service": str, "cost": int, "note": str}
medicines = []    # mỗi item: {"id": int, "name": str, "dosage": str, "days": int, "unit": str}

# Helper để tạo id tự tăng
def next_id(collection):
    return (collection[-1]["id"] + 1) if collection else 1

@app.route("/")
def home():
    # Hiển thị home (nếu muốn hiển tên khi đã login có thể truyền session)
    username = session.get("user")
    return render_template("home.html", username=username)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        username = request.form["username"]
        password = request.form["password"]
        confirm = request.form["confirm"]

        if password != confirm:
            return "Xác nhận mật khẩu không khớp!"
        if username in users:
            return "Tài khoản đã tồn tại!"

        users[username] = {"name": name, "email": email, "password": password}
        return redirect("/login")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Demo nhanh: nếu có username field thì dùng, nếu không lấy default "Bác sĩ"
        username = request.form.get("username") or request.form.get("email") or "Bác sĩ"
        session["user"] = username
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    username = session["user"]
    return render_template("dashboard.html", username=username)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

# ---------- Treatment (Lập phiếu điều trị) ----------
@app.route("/treatment", methods=["GET"])
def treatment():
    if "user" not in session:
        return redirect(url_for("login"))
    username = session["user"]
    return render_template("treatment.html", username=username, treatments=treatments)

@app.route("/treatment/add", methods=["POST"])
def treatment_add():
    if "user" not in session:
        return redirect(url_for("login"))
    service = request.form.get("service", "").strip()
    cost = request.form.get("cost", "0").strip()
    note = request.form.get("note", "").strip()
    try:
        cost_val = int(cost)
    except:
        cost_val = 0
    item = {
        "id": next_id(treatments),
        "service": service,
        "cost": cost_val,
        "note": note
    }
    treatments.append(item)
    return redirect(url_for("treatment"))

@app.route("/treatment/delete/<int:item_id>", methods=["POST", "GET"])
def treatment_delete(item_id):
    global treatments
    treatments = [t for t in treatments if t["id"] != item_id]
    return redirect(url_for("treatment"))

# ---------- Medicine (Quản lý thuốc) ----------
@app.route("/medicine", methods=["GET"])
def medicine():
    if "user" not in session:
        return redirect(url_for("login"))
    username = session["user"]
    return render_template("medicine.html", username=username, medicines=medicines)

@app.route("/medicine/add", methods=["POST"])
def medicine_add():
    if "user" not in session:
        return redirect(url_for("login"))
    name = request.form.get("name", "").strip()
    dosage = request.form.get("dosage", "").strip()
    days = request.form.get("days", "0").strip()
    unit = request.form.get("unit", "").strip()
    try:
        days_val = int(days)
    except:
        days_val = 0
    item = {
        "id": next_id(medicines),
        "name": name,
        "dosage": dosage,
        "days": days_val,
        "unit": unit
    }
    medicines.append(item)
    return redirect(url_for("medicine"))

@app.route("/medicine/delete/<int:item_id>", methods=["POST", "GET"])
def medicine_delete(item_id):
    global medicines
    medicines = [m for m in medicines if m["id"] != item_id]
    return redirect(url_for("medicine"))

if __name__ == "__main__":
    app.run(debug=True)
