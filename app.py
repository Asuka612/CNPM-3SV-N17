import hashlib
from os.path import exists
import pdb

from flask import Flask, render_template, request, redirect, session, url_for, flash
import math
import dao
from __init__ import app, login, db  # , admin
from flask_login import login_user, current_user, logout_user
import os
import json
from datetime import datetime
from models import TaiKhoan, UserRole, NguoiDung, GioiTinh, KhachHang, LichKham

# Load dữ liệu dịch vụ từ file JSON
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
SERVICES_FILE = os.path.join(DATA_DIR, "DichVu.json")

@app.context_processor
def inject_globals():
    return {
        "services": dao.load_dich_vu(),
        "medicines": dao.load_dich_vu(),
        "UserRole": UserRole,
        "gioitinh": GioiTinh,
        "dentists": dao.load_nhasi()
    }

# Helper tạo ID tự tăng
def next_id(collection):
    return (collection[-1]["id"] + 1) if collection else 1

@app.route("/")
def home():
    page = request.args.get("page")
    return render_template("home.html", page=page)

@app.route("/service/<ma>")
def service_detail(ma):
    service = next((s for s in dao.load_dich_vu() if s.MaDichVu == ma), None)
    return render_template("service_detail.html", service=service)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        gmail = request.form["email"]
        password = request.form["password"]
        confirm = request.form["confirm"]

        if password != confirm:
            flash("Xác nhận mật khẩu không khớp!", "danger")
        else:
            existing_user = TaiKhoan.query.filter(TaiKhoan.Email == gmail).first()
            if existing_user:
                flash("Tài khoản này đã được đăng ký", "danger")
            else:
                password = hashlib.md5(password.encode("utf-8")).hexdigest()
                nguoidung = KhachHang(
                    HoVaTen=name
                )
                taikhoan = TaiKhoan(
                    Email=gmail,
                    MatKhau=password,
                    nguoi_dung = nguoidung
                )
                try:
                    db.session.add(taikhoan)
                    db.session.add(nguoidung)
                    db.session.commit()
                    flash("Đăng ký thành công! Vui lòng đăng nhập để tiếp tục!", "success")
                    return redirect('/login')
                except:
                    db.session.rollback()
                    flash("Hệ thống đã bị lỗi! Xin vui lòng thử lại sau", "danger")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login_my_user():
    if current_user.is_authenticated:
        return redirect("/")

    err_msg = None

    if request.method == "POST":
        gmail = request.form.get('gmail')
        password = request.form.get('password')

        user = dao.auth_user(gmail, password)

        if user:

            login_user(user)

            if user.Role == UserRole.ADMIN:
                return redirect('/Admin')
            elif user.Role == UserRole.NHASI:
                return redirect('/dashboard')
            else:
                return redirect('/MakeAppointment')
        else:
            err_msg = "Tài khoản hoặc mật khẩu không đúng!"

    return render_template("login.html", err_msg=err_msg)


@app.route("/dashboard")
def dashboard():
    username = current_user.nguoi_dung.HoVaTen
    return render_template("dashboard.html", username=username)


@app.route('/logout')
def logout_my_user():
    logout_user()
    return redirect('/')


# ------------------- Treatment -------------------
@app.route("/treatment")
def treatment():
    username = current_user.nguoi_dung.HoVaTen
    return render_template("treatment.html", username=username)


@app.route("/treatment/add", methods=["POST"])
def treatment_add():
    service = request.form.get("service")
    cost = request.form.get("cost", "0").strip()
    note = request.form.get("note", "").strip()
    try:
        cost_val = int(cost)
    except:
        cost_val = 0
    item = {"id": next_id(service), "service": service, "cost": cost_val, "note": note}
    treatments.append(item)
    return redirect('/treatment')

@app.route("/treatment/delete/<int:item_id>", methods=["POST"])
def treatment_delete(item_id):
    global treatments
    treatments = [t for t in treatments if t["id"] != item_id]
    return redirect('/treatment')

# ------------------- Medicine -------------------
@app.route("/medicine")
def medicine():
    username = current_user.nguoi_dung.HoVaTen
    # Lấy danh sách thuốc từ CSDL
    available_medicines = dao.load_thuoc()
    return render_template("medicine.html", username=username, medicines=medicines, available_medicines=available_medicines)



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
    item = {"id": next_id(medicines), "name": name, "dosage": dosage, "days": days_val, "unit": unit}
    medicines.append(item)
    return redirect('/medicine')


@app.route("/medicine/delete/<int:item_id>", methods=["POST"])
def medicine_delete(item_id):
    global medicines
    medicines = [m for m in medicines if m["id"] != item_id]
    return redirect('/medicine')



# ------------------- Appointment -------------------
@app.route("/MakeAppointment", methods=["GET", "POST"])
def appointment():
    # Phần xử lý POST: Đặt lịch
    if request.method == "POST":
        # 1. Lấy dữ liệu từ form
        name = request.form.get("name")
        day = request.form.get("day")  # Ví dụ: '2025-12-20'
        time = request.form.get("time")  # Ví dụ: '09:30'
        dentist_id = request.form.get("dentist")  # ID bác sĩ
        service_id = request.form.get("service")

        # 2. KIỂM TRA TRÙNG LỊCH (Logic quan trọng nhất)
        # Tìm xem trong DB đã có lịch nào của Bác sĩ này + Ngày này + Giờ này chưa
        lich_trung = LichKham.query.filter(
            LichKham.NhaSiId == dentist_id,
            LichKham.NgayKham == day,
            LichKham.GioKham == time
        ).first()

        if lich_trung:
            # 3a. Nếu trùng: Báo lỗi và không lưu
            flash(f"Bác sĩ đã có lịch hẹn vào lúc {time} ngày {day}. Vui lòng chọn giờ khác!", "danger")
            # Tải lại trang để người dùng chọn lại
            return redirect("/MakeAppointment")  # Hoặc render_template lại

        else:
            # 3b. Nếu không trùng: Tiến hành lưu
            try:
                # Tạo đối tượng khách hàng (nếu chưa có logic đăng nhập)
                # Hoặc lấy current_user.id nếu đã đăng nhập

                # Tạo lịch hẹn mới
                new_appointment = LichKham(
                    KhachHangId=current_user.id,  # Giả sử đang dùng flask_login
                    NhaSiId=dentist_id,
                    DichVuId=service_id,
                    NgayKham=day,
                    GioKham=time,
                )
                db.session.add(new_appointment)
                db.session.commit()

                flash("Đặt lịch thành công!", "success")
                return redirect('/')

            except Exception as e:
                db.session.rollback()
                print(e)
                flash("Có lỗi xảy ra khi lưu dữ liệu.", "danger")
                return redirect("/MakeAppointment")

    return render_template("MakeAppointment.html")



@login.user_loader
def get_user(user_id):
    return dao.get_user_by_id(user_id)


# ------------------- Cashier / Bills -------------------
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

    return render_template("cashier.html", treatments=treatments, medicines=medicines)



if __name__ == "__main__":
    app.run(debug=True)
