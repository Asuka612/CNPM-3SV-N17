import hashlib
from os.path import exists
import pdb
from __init__ import app
from werkzeug.utils import secure_filename
import math
import pdb
import os
import json
import dao
from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
from __init__ import app, login, db  # , admin
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime
from sqlalchemy import func, extract
from models import TaiKhoan, GioiTinh, UserRole, NhaSi, KhachHang, KeToan, LichKham, PhieuDieuTri, ChiTietPhieuDieuTri, \
    DichVu, Thuoc, LoThuoc, ChiTietToaThuoc, NguoiDung, ToaThuoc

# Load dữ liệu dịch vụ từ file JSON

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
SERVICES_FILE = os.path.join(DATA_DIR, "DichVu.json")


@app.context_processor
def inject_globals():
    return {
        "services": dao.load_dich_vu(),
        "medicines": dao.load_dich_vu(),
        "customers": dao.load_nguoi_dung(),
        "dentists": dao.load_nhasi(),
        "UserRole": UserRole,
        "gioitinh": GioiTinh

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
                    nguoi_dung=nguoidung
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
                return redirect('/admin')  # chữ thường
            elif user.Role == UserRole.NHASI:
                return redirect('/dashboard')
            elif user.Role == UserRole.KETOAN:
                return redirect('/cashier')
            else:
                return redirect('/MakeAppointment')
        else:
            err_msg = "Tài khoản hoặc mật khẩu không đúng!"

    return render_template("login.html", err_msg=err_msg)


@app.route('/logout')
def logout_my_user():
    logout_user()
    return redirect('/')


@app.route("/dashboard")
def dashboard():
    username = current_user.nguoi_dung.HoVaTen
    return render_template("dashboard.html", username=username)


# ------------------- Treatment -------------------
@app.route("/treatment/create", methods=["GET", "POST"])
def create_treatment():
    username = current_user.nguoi_dung.HoVaTen
    den_cus = dao.load_khach_hang_with_nha_si(current_user.id)
    if request.method == "POST":
        nha_si_id = current_user.id
        khach_hang_id = request.form.get("customer_id")
        chan_doan = request.form.get("diagnosis")

        # 1. Tạo Phiếu Điều Trị (Master)
        new_phieu = PhieuDieuTri(
            NhaSiId=nha_si_id,
            KhachHangId=khach_hang_id,
            ChuanDoan=chan_doan
        )
        try:
            db.session.add(new_phieu)
            db.session.commit()
            return redirect(url_for('treatment_detail', phieu_id=new_phieu.id))
        except Exception as e:
            db.session.rollback()
            flash("Lỗi khi tạo phiếu: " + str(e), "danger")

    return render_template("treatment.html", username=username, den_cus=den_cus)


# --- ROUTE 2: CHI TIẾT PHIẾU & THÊM DỊCH VỤ (Bước 2) ---
@app.route("/treatment/detail/<int:phieu_id>", methods=["GET", "POST"])
def treatment_detail(phieu_id):
    # Lấy thông tin phiếu để hiển thị
    phieu = PhieuDieuTri.query.get_or_404(phieu_id)

    # XỬ LÝ POST: Khi bác sĩ thêm dịch vụ vào phiếu này
    if request.method == "POST":
        dich_vu_id = request.form.get("service_id")
        so_luong = request.form.get("times")
        ghi_chu = request.form.get("note")
        try:
            exists = ChiTietPhieuDieuTri.query.filter_by(
                PhieuDieuTriId=phieu.id,
                DichVuId=dich_vu_id
            ).first()
            if exists:
                flash("Dịch vụ này đã có trong phiếu, vui lòng chỉnh sửa số lượng thay vì thêm mới.", "warning")
            else:
                # 2. Tạo Chi Tiết Phiếu (Detail)
                new_detail = ChiTietPhieuDieuTri(
                    PhieuDieuTriId=phieu.id,  # Lấy ID từ phiếu hiện tại
                    DichVuId=dich_vu_id,
                    SoLuong=so_luong,
                    GhiChu=ghi_chu
                )
                db.session.add(new_detail)
                db.session.commit()
                flash("Đã thêm dịch vụ thành công!", "success")
        except Exception as e:
            db.session.rollback()
            flash("Lỗi thêm dịch vụ (có thể đã trùng dịch vụ): " + str(e), "danger")

        # Redirect lại chính trang này để refresh danh sách
        return redirect(url_for('treatment_detail', phieu_id=phieu_id))

    # XỬ LÝ GET: Hiển thị form và danh sách dịch vụ
    ds_dich_vu = DichVu.query.all()

    # Lấy danh sách các chi tiết đã thêm để hiển thị bên dưới (nếu cần)
    ds_chi_tiet = ChiTietPhieuDieuTri.query.filter_by(PhieuDieuTriId=phieu_id).all()

    return render_template("treatment-detail.html",
                           phieu=phieu,
                           services=ds_dich_vu,
                           details=ds_chi_tiet)


@app.route("/treatment/delete-detail/<int:phieu_id>/<int:dich_vu_id>", methods=["POST"])
def delete_treatment_detail(phieu_id, dich_vu_id):
    chi_tiet = ChiTietPhieuDieuTri.query.get_or_404((phieu_id, dich_vu_id))
    try:
        db.session.delete(chi_tiet)
        db.session.commit()
        flash("Đã xóa dịch vụ khỏi phiếu!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Lỗi khi xóa: " + str(e), "danger")

    # Redirect về lại trang chi tiết phiếu
    return redirect(url_for('treatment_detail', phieu_id=phieu_id))


# ------------------- Medicine -------------------
# app.py

@app.route("/medicine/<int:phieu_id>")  # Nhận ID phiếu điều trị từ URL
def medicine_page(phieu_id):
    # 1. Kiểm tra xem phiếu điều trị này đã có toa thuốc chưa
    # (Dựa trên quan hệ 1-1 hoặc 1-n trong Model của bạn)
    toa_thuoc = ToaThuoc.query.filter_by(PhieuDieuTriId=phieu_id).first()

    # 2. Nếu chưa có thì TẠO MỚI ngay lập tức
    if not toa_thuoc:
        toa_thuoc = ToaThuoc(PhieuDieuTriId=phieu_id)
        db.session.add(toa_thuoc)
        db.session.commit()
        # Lúc này toa_thuoc.id đã được sinh ra tự động

    # 3. Lấy danh sách thuốc trong kho (để hiện Dropdown chọn)
    medicines_data = dao.get_available_medicines()

    # 4. Lấy danh sách thuốc ĐÃ KÊ trong toa này (để hiện Bảng bên dưới)
    # Lưu ý: Truyền đúng biến toa_thuoc object sang HTML
    return render_template("medicine.html",
                           toa_thuoc=toa_thuoc,  # Truyền object ToaThuoc sang
                           medicines=medicines_data)


@app.route("/medicine/add", methods=["POST"])
def medicine_add():
    try:
        toa_thuoc_id = request.form.get("toa_thuoc_id")
        current_toa = dao.get_toa_thuoc_by_id(toa_thuoc_id)
        thuoc_id = int(request.form.get("thuoc_id"))
        lieu_dung = float(request.form.get("lieu_dung"))
        so_ngay = int(request.form.get("so_ngay"))
        ghi_chu = request.form.get("ghi_chu")

        # 1. Tính số lượng MỚI đang muốn thêm
        so_luong_moi = int(math.ceil(lieu_dung * so_ngay))

        # 2. Tính số lượng thuốc này ĐÃ CÓ trong bảng kê (nhưng chưa lưu kho)
        # Tìm xem trong toa này đã kê thuốc này chưa để cộng dồn
        existing_item = ChiTietToaThuoc.query.filter_by(
            ToaThuocId=toa_thuoc_id,
            ThuocId=thuoc_id
        ).first()

        so_luong_da_ke = existing_item.SoLuong if existing_item else 0

        # 3. Lấy tồn kho thực tế
        # Lưu ý: Hàm này trả về list tuple, cần tìm đúng thuốc
        available_list = dao.get_available_medicines()
        selected_med = next((item for item in available_list if item[0].id == thuoc_id), None)


        if not selected_med:
            return "Thuốc không hợp lệ", 400

        real_stock = selected_med.total_stock

        # 4. KIỂM TRA LOGIC: Tổng (Đã kê + Mới) không được vượt quá Tồn kho
        total_request = so_luong_da_ke + so_luong_moi

        if total_request > real_stock:
            flash(f"Kho chỉ còn {real_stock}. Trong toa đã có {so_luong_da_ke}, thêm {so_luong_moi} nữa là quá tải!",
                  "error")
            return redirect(url_for('medicine_page'))

        # 5. Lưu vào DB (Nếu đã có thì cập nhật cộng dồn, chưa có thì thêm mới)
        if existing_item:
            existing_item.SoLuong += so_luong_moi
            existing_item.ThanhTien = existing_item.SoLuong * selected_med[0].GiaBan
            # Cập nhật các trường khác nếu cần
        else:
            new_detail = ChiTietToaThuoc(
                ToaThuocId=toa_thuoc_id,
                ThuocId=thuoc_id,
                LieuDung=lieu_dung,
                SoNgay=so_ngay,
                SoLuong=so_luong_moi,
                GhiChu=ghi_chu,
                ThanhTien=so_luong_moi * selected_med[0].GiaBan
            )


            db.session.add(new_detail)



        db.session.commit()
        flash("Đã thêm vào bảng kê (Chưa trừ kho).", "success")
        return redirect(url_for('medicine_page',phieu_id=current_toa.PhieuDieuTriId))

    except Exception as e:
        db.session.rollback()
        print(e)
        return "Lỗi hệ thống", 500


@app.route("/medicine/delete/<int:thuoc_id>", methods=["POST"])
def medicine_delete(thuoc_id):
    try:
        toa_thuoc_id = request.form.get("toa_thuoc_id")
        current_toa = dao.get_toa_thuoc_by_id(toa_thuoc_id)

        detail = ChiTietToaThuoc.query.filter_by(ToaThuocId=toa_thuoc_id, ThuocId=thuoc_id).first()

        if detail:
            db.session.delete(detail)
            db.session.commit()
            flash("Đã xóa khỏi bảng kê.", "info")
            # KHÔNG GỌI dao.restore_stock VÌ CHƯA TRỪ

        return redirect(url_for('medicine_page',phieu_id=current_toa.PhieuDieuTriId))
    except Exception as e:
        print(e)
        return "Lỗi xóa", 500


@app.route("/medicine/save", methods=["POST"])
def medicine_save():
    try:
        toa_thuoc_id = request.form.get("toa_thuoc_id")
        current_toa = dao.get_toa_thuoc_by_id(toa_thuoc_id)

        # 1. Lấy tất cả chi tiết trong toa
        details = ChiTietToaThuoc.query.filter_by(ToaThuocId=toa_thuoc_id).all()

        if not details:
            flash("Toa thuốc trống, không thể lưu!", "warning")
            return redirect(url_for('medicine_page',phieu_id=current_toa.PhieuDieuTriId))

        # 2. Duyệt qua từng thuốc để trừ kho
        # Dùng transaction để đảm bảo: Trừ thành công hết mới lưu, lỗi 1 cái là hoàn tác hết
        error_occurred = False

        for item in details:
            # Gọi hàm trừ kho FIFO cho từng món
            # Hàm này trả về True/False (bạn cần sửa hàm dao để trả về boolean như hướng dẫn trước)
            # Hoặc kiểm tra exception

            # Check tồn kho lần cuối trước khi trừ thật
            stock_ok = dao.deduct_stock_fifo(item.ThuocId, item.SoLuong)

            if not stock_ok:
                error_occurred = True
                flash(f"Lỗi: Thuốc ID {item.ThuocId} không đủ tồn kho để xuất!", "error")
                break  # Dừng lại ngay

        if error_occurred:
            # Nếu có lỗi, rollback toàn bộ quá trình trừ kho nãy giờ
            db.session.rollback()
            return redirect(url_for('medicine_page',phieu_id=current_toa.PhieuDieuTriId))

        # 3. Nếu mọi thứ OK
        # Có thể cập nhật trạng thái ToaThuoc là "DA_HOAN_THANH" nếu bạn có cột status
        # toa = ToaThuoc.query.get(toa_thuoc_id)
        # toa.TrangThai = 'DONE'

        db.session.commit()  # Chốt trừ kho
        flash("Đã lưu toa thuốc và xuất kho thành công!", "success")

        # Chuyển hướng về trang danh sách bệnh nhân hoặc in hóa đơn
        return redirect(url_for('medicine_page', phieu_id=current_toa.PhieuDieuTriId))  # Hoặc url_for('invoice_page')

    except Exception as e:
        db.session.rollback()
        print(e)
        flash("Có lỗi xảy ra khi lưu toa.", "error")
        return redirect(url_for('medicine_page'))


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
            try:
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
    services = dao.load_dich_vu()
    medicines = dao.load_thuoc()
    if request.method == "POST":
        name = request.form.get("patient_name", "Khách")
        selected_treat_ids = request.form.getlist("treat_ids")
        selected_med_ids = request.form.getlist("med_ids")

        selected_treats = [t for t in services if str(t["id"]) in selected_treat_ids]
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

    return render_template("cashier.html", services=services, medicines=medicines)


@app.route("/profile")
def profile():
    if not current_user.is_authenticated:
        return redirect("/login")
    return render_template("profile.html", user=current_user)


@app.route("/profile/update", methods=["POST"])
def profile_update():
    if not current_user.is_authenticated:
        return redirect("/login")

    user = current_user

    # Lấy dữ liệu từ form
    user.nguoi_dung.HoVaTen = request.form.get("HoVaTen")
    user.nguoi_dung.GioiTinh = request.form.get("GioiTinh")
    ngay_sinh = request.form.get("NgaySinh")
    if ngay_sinh:
        user.nguoi_dung.NgaySinh = datetime.strptime(ngay_sinh, "%Y-%m-%d").date()
    user.nguoi_dung.SDT = request.form.get("SDT")

    # Xử lý upload avatar nếu có
    avatar_file = request.files.get("Avatar")
    if avatar_file and avatar_file.filename != "":
        filename = secure_filename(avatar_file.filename)
        avatar_path = os.path.join("static", "uploads", filename)
        avatar_file.save(avatar_path)
        user.Avatar = "/" + avatar_path.replace("\\", "/")  # Đường dẫn URL

    try:
        db.session.commit()
        flash("Cập nhật thông tin thành công!", "success")
    except:
        db.session.rollback()
        flash("Có lỗi xảy ra, vui lòng thử lại.", "danger")

    return redirect("/profile")


@app.route("/admin")
def admin_dashboard():
    if not current_user.is_authenticated or current_user.Role != UserRole.ADMIN:
        return redirect("/login")

    # 1. Tổng số nhân sự
    total_doctors = NhaSi.query.filter_by(active=True).count()
    total_patients = KhachHang.query.filter_by(active=True).count()
    total_accountants = KeToan.query.filter_by(active=True).count()

    # 2. Lịch hẹn
    today = datetime.today().date()
    week_num = today.isocalendar()[1]
    appointments_today = LichKham.query.filter(LichKham.NgayKham == today).count()
    appointments_week = LichKham.query.filter(
        extract('week', LichKham.NgayKham) == week_num,
        extract('year', LichKham.NgayKham) == today.year
    ).count()
    appointments_month = LichKham.query.filter(
        extract('month', LichKham.NgayKham) == today.month,
        extract('year', LichKham.NgayKham) == today.year
    ).count()

    # 3. Hóa đơn và doanh thu (fix join với DichVu)
    revenue_today = db.session.query(
        func.sum(ChiTietPhieuDieuTri.SoLuong * DichVu.ChiPhi)
    ).join(PhieuDieuTri, ChiTietPhieuDieuTri.PhieuDieuTriId == PhieuDieuTri.id) \
                        .join(DichVu, ChiTietPhieuDieuTri.DichVuId == DichVu.id) \
                        .filter(PhieuDieuTri.created_date == today).scalar() or 0

    revenue_week = db.session.query(
        func.sum(ChiTietPhieuDieuTri.SoLuong * DichVu.ChiPhi)
    ).join(PhieuDieuTri, ChiTietPhieuDieuTri.PhieuDieuTriId == PhieuDieuTri.id) \
                       .join(DichVu, ChiTietPhieuDieuTri.DichVuId == DichVu.id) \
                       .filter(
        extract('week', PhieuDieuTri.created_date) == week_num,
        extract('year', PhieuDieuTri.created_date) == today.year
    ).scalar() or 0

    revenue_month = db.session.query(
        func.sum(ChiTietPhieuDieuTri.SoLuong * DichVu.ChiPhi)
    ).join(PhieuDieuTri, ChiTietPhieuDieuTri.PhieuDieuTriId == PhieuDieuTri.id) \
                        .join(DichVu, ChiTietPhieuDieuTri.DichVuId == DichVu.id) \
                        .filter(
        extract('month', PhieuDieuTri.created_date) == today.month,
        extract('year', PhieuDieuTri.created_date) == today.year
    ).scalar() or 0

    # Số hóa đơn
    bills_today = PhieuDieuTri.query.filter(PhieuDieuTri.created_date == today).count()
    bills_week = PhieuDieuTri.query.filter(
        extract('week', PhieuDieuTri.created_date) == week_num,
        extract('year', PhieuDieuTri.created_date) == today.year
    ).count()
    bills_month = PhieuDieuTri.query.filter(
        extract('month', PhieuDieuTri.created_date) == today.month,
        extract('year', PhieuDieuTri.created_date) == today.year
    ).count()

    # 4. Dịch vụ phổ biến
    popular_services = db.session.query(
        DichVu.TenDichVu, func.count(ChiTietPhieuDieuTri.DichVuId)
    ).join(ChiTietPhieuDieuTri, ChiTietPhieuDieuTri.DichVuId == DichVu.id) \
        .group_by(DichVu.TenDichVu) \
        .order_by(func.count(ChiTietPhieuDieuTri.DichVuId).desc()).limit(10).all()

    # 5. Thuốc bán chạy
    top_medicines = db.session.query(
        Thuoc.TenThuoc, func.sum(ChiTietToaThuoc.SoLuong)
    ).join(ChiTietToaThuoc, ChiTietToaThuoc.ThuocId == Thuoc.id) \
        .group_by(Thuoc.TenThuoc) \
        .order_by(func.sum(ChiTietToaThuoc.SoLuong).desc()).limit(10).all()

    # Thuốc tồn kho thấp
    low_stock_medicines = LoThuoc.query.filter(LoThuoc.SoLuongTon <= 10).all()

    stats = {
        "total_doctors": total_doctors,
        "total_patients": total_patients,
        "total_accountants": total_accountants,
        "appointments_today": appointments_today,
        "appointments_week": appointments_week,
        "appointments_month": appointments_month,
        "bills_today": bills_today,
        "revenue_today": revenue_today,
        "bills_week": bills_week,
        "revenue_week": revenue_week,
        "bills_month": bills_month,
        "revenue_month": revenue_month,
        "popular_services": popular_services,
        "top_medicines": top_medicines,
        "low_stock_medicines": low_stock_medicines
    }

    return render_template("Admin/admin.html", stats=stats)


@app.route("/admin/users/staff")
def admin_staff():
    if not current_user.is_authenticated or current_user.Role != UserRole.ADMIN:
        return redirect("/login")

    doctors = NhaSi.query.filter_by(active=True).all()
    accountants = KeToan.query.filter_by(active=True).all()

    return render_template(
        "Admin/admin_staff.html",
        doctors=doctors,
        accountants=accountants
    )


@app.route("/admin/users/customers")
def admin_customers():
    if not current_user.is_authenticated or current_user.Role != UserRole.ADMIN:
        return redirect("/login")

    customers = KhachHang.query.filter_by(active=True).all()

    return render_template(
        "Admin/admin_customers.html",
        customers=customers
    )


@app.route('/admin/services')
@login_required
def admin_services():
    if current_user.Role != UserRole.ADMIN:
        return "Unauthorized", 403

    services = DichVu.query.all()
    return render_template('admin/services.html', services=services)


@app.route("/admin/services/add", methods=["GET", "POST"])
@login_required
def admin_add_service():
    if current_user.Role != UserRole.ADMIN:
        return "Unauthorized", 403

    if request.method == "POST":
        ten = request.form.get("TenDichVu")
        chiphi = request.form.get("ChiPhi")
        mota = request.form.get("MoTa")

        try:
            dv = DichVu(
                TenDichVu=ten,
                ChiPhi=float(chiphi),
                MoTa=mota
            )
            db.session.add(dv)
            db.session.commit()
            flash("Thêm dịch vụ thành công!", "success")
            return redirect("/admin/services")
        except Exception as e:
            db.session.rollback()
            flash("Lỗi thêm dịch vụ: " + str(e), "danger")

    return render_template("Admin/service_add.html")


@app.route("/admin/services/edit/<int:service_id>", methods=["GET", "POST"])
@login_required
def admin_edit_service(service_id):
    if current_user.Role != UserRole.ADMIN:
        return "Unauthorized", 403

    dv = DichVu.query.get_or_404(service_id)

    if request.method == "POST":
        dv.TenDichVu = request.form.get("TenDichVu")
        dv.ChiPhi = float(request.form.get("ChiPhi"))
        dv.MoTa = request.form.get("MoTa")

        try:
            db.session.commit()
            flash("Cập nhật dịch vụ thành công!", "success")
            return redirect("/admin/services")
        except Exception as e:
            db.session.rollback()
            flash("Lỗi cập nhật: " + str(e), "danger")

    return render_template("Admin/service_edit.html", dv=dv)


@app.route("/admin/services/delete/<int:service_id>")
@login_required
def admin_delete_service(service_id):
    if current_user.Role != UserRole.ADMIN:
        return "Unauthorized", 403

    dv = DichVu.query.get_or_404(service_id)

    # Kiểm tra dịch vụ đã được dùng chưa
    used = ChiTietPhieuDieuTri.query.filter_by(DichVuId=service_id).first()
    if used:
        flash("Không thể xóa! Dịch vụ đã được sử dụng.", "danger")
        return redirect("/admin/services")

    try:
        db.session.delete(dv)
        db.session.commit()
        flash("Xóa dịch vụ thành công!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Lỗi xóa dịch vụ: " + str(e), "danger")

    return redirect("/admin/services")


@app.route("/admin/lo-thuoc")
@login_required
def admin_lo_thuoc():
    if current_user.Role.name != "ADMIN":
        return redirect("/")

    lo_thuoc = LoThuoc.query.all()
    return render_template("admin/lo_thuoc.html", lo_thuoc=lo_thuoc)


@app.route("/admin/lo-thuoc/add", methods=["POST"])
@login_required
def add_lo_thuoc():
    if current_user.Role.name != "ADMIN":
        return redirect("/")

    ma_lo = request.form.get("ma_lo_thuoc")
    thuoc_id = request.form.get("thuoc_id")
    so_luong_nhap = request.form.get("so_luong_nhap")
    so_luong_ton = request.form.get("so_luong_ton")
    han_su_dung = request.form.get("han_su_dung")

    lo = LoThuoc(
        MaLoThuoc=ma_lo,
        ThuocId=thuoc_id,
        SoLuongNhap=so_luong_nhap,
        SoLuongTon=so_luong_ton,
        HanSuDung=datetime.strptime(han_su_dung, "%Y-%m-%d") if han_su_dung else None
    )

    db.session.add(lo)
    db.session.commit()

    return redirect("/admin/lo-thuoc")


@app.route("/admin/lo-thuoc/delete/<string:ma_lo>")
@login_required
def delete_lo_thuoc(ma_lo):
    if current_user.Role.name != "ADMIN":
        return redirect("/")

    lo = LoThuoc.query.get(ma_lo)
    if lo:
        db.session.delete(lo)
        db.session.commit()

    return redirect("/admin/lo-thuoc")


@app.route("/admin/accounts")
@login_required
def admin_accounts():
    if current_user.Role != UserRole.ADMIN:
        return redirect("/")

    accounts = TaiKhoan.query.all()
    nguoidung_chua_co_tk = NguoiDung.query.filter(~NguoiDung.id.in_(
        db.session.query(TaiKhoan.NguoiDungId)
    )).all()

    return render_template(
        "Admin/admin_accounts.html",
        accounts=accounts,
        nguoidung_chua_co_tk=nguoidung_chua_co_tk
    )


@app.route("/admin/accounts/add", methods=["POST"])
@login_required
def admin_add_account():
    if current_user.Role != UserRole.ADMIN:
        return redirect("/")

    nguoidung_id = request.form.get("nguoidung_id")
    email = request.form.get("email")
    password = request.form.get("password")
    role = request.form.get("role")

    hashed = hashlib.md5(password.encode("utf-8")).hexdigest()

    tk = TaiKhoan(
        NguoiDungId=nguoidung_id,
        Email=email,
        MatKhau=hashed,
        Role=UserRole[role]
    )

    try:
        db.session.add(tk)
        db.session.commit()
        flash("Thêm tài khoản thành công!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Lỗi thêm tài khoản: " + str(e), "danger")

    return redirect("/admin/accounts")


@app.route("/admin/accounts/delete/<int:account_id>")
@login_required
def admin_delete_account(account_id):
    if current_user.Role != UserRole.ADMIN:
        return redirect("/")

    tk = TaiKhoan.query.get_or_404(account_id)

    try:
        db.session.delete(tk)
        db.session.commit()
        flash("Xóa tài khoản thành công!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Không thể xóa tài khoản: " + str(e), "danger")

    return redirect("/admin/accounts")


if __name__ == "__main__":
    app.run(debug=True)
