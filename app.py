from flask import Flask, render_template, request, redirect, session, url_for
import math
import dao
from __init__ import app, login #, admin
from flask_login import login_user, current_user, logout_user

from models import User, UserRole

# app = Flask(__name__)
# app.secret_key = "secret_key_here"

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
    # username = current_user.username
    page = request.args.get("page")
    return render_template("home.html", page=page) #, username=username

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
def login_my_user():
    if current_user.is_authenticated:
        return redirect("/")

    err_msg = None

    if request.method.__eq__('POST'):
        gmail = request.form.get('gmail')
        password = request.form.get('password')

        user = dao.auth_user(gmail, password)

        if user:
            login_user(user)
            if user.role == UserRole.ADMIN:
                return redirect('/dashboard')  # Trang dành cho admin
            else:
                return redirect('/')  # Trang dành cho quản lý/chuyên môn

        else:
            err_msg = "Tài khoản hoặc mật khẩu không đúng!"
    return render_template("login.html", err_msg=err_msg)

@app.route("/dashboard")
def dashboard():
    username = current_user.name
    return render_template("dashboard.html", username=username)

@app.route('/logout')
def logout_my_user():
    logout_user()
    return redirect('/')

# ---------- Treatment (Lập phiếu điều trị) ----------
@app.route("/treatment", methods=["GET"])
def treatment():
    username = current_user.name
    return render_template("treatment.html", username=username, treatments=treatments)

@app.route("/treatment/add", methods=["POST"])
def treatment_add():
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
    return redirect('/treatment')

@app.route("/treatment/delete/<int:item_id>", methods=["POST", "GET"])
def treatment_delete(item_id):
    global treatments
    treatments = [t for t in treatments if t["id"] != item_id]
    return redirect('/treatment')

# ---------- Medicine (Quản lý thuốc) ----------
@app.route("/medicine", methods=["GET"])
def medicine():
    username = current_user.name
    return render_template("medicine.html", username=username, medicines=medicines)

@app.route("/medicine/add", methods=["POST"])
def medicine_add():
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
    return redirect('/medicine')

@app.route("/medicine/delete/<int:item_id>", methods=["POST", "GET"])
def medicine_delete(item_id):
    global medicines
    medicines = [m for m in medicines if m["id"] != item_id]
    return redirect('/medicine')

@app.route("/MakeAppointment.html")
def appointment():
    page = request.args.get("page")
    pages = int(page) if page is not None else 1
    return render_template("MakeAppointment.html", pages=pages)

@login.user_loader
def get_user(user_id):
    return dao.get_user_by_id(user_id)
import os
import json
from datetime import datetime
from flask import render_template, request, redirect

# ======================
# CASHIER SECTION (THU NGÂN)
# ======================

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
BILLS_FILE = os.path.join(DATA_DIR, "bills.json")


def load_bills():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(BILLS_FILE):
        with open(BILLS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
    with open(BILLS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_bills(bills):
    with open(BILLS_FILE, "w", encoding="utf-8") as f:
        json.dump(bills, f, ensure_ascii=False, indent=2)


@app.route("/cashier", methods=["GET", "POST"])
def cashier_page():
    if request.method == "POST":
        name = request.form.get("patient_name", "Khách")
        selected_treat_ids = request.form.getlist("treat_ids")
        selected_med_ids = request.form.getlist("med_ids")

        selected_treats = [t for t in treatments if str(t["id"]) in selected_treat_ids]
        selected_medicines = [m for m in medicines if str(m["id"]) in selected_med_ids]

        total_treat = sum(t.get("cost", 0) for t in selected_treats)
        total_med = sum(m.get("price", 0) for m in selected_medicines)
        total = total_treat + total_med

        bill = {
            "id": int(datetime.now().timestamp()),
            "patient_name": name,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "treatments": selected_treats,
            "medicines": selected_medicines,
            "total": total
        }

        bills = load_bills()
        bills.append(bill)
        save_bills(bills)

        return render_template("receipt.html", bill=bill)

    return render_template("cashier.html",
                           treatments=treatments,
                           medicines=medicines)

if __name__ == "__main__":
    app.run(debug=True)
