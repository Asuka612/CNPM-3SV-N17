import hashlib
from werkzeug.utils import secure_filename
import math
import os
import dao
from flask import render_template, request, redirect, url_for, jsonify, flash
from __init__ import app, login, db
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime
from sqlalchemy import func, extract, or_, text
from models import TaiKhoan, GioiTinh, UserRole, NhaSi, KhachHang, KeToan, LichKham, PhieuDieuTri, ChiTietPhieuDieuTri, \
    DichVu, Thuoc, LoThuoc, ChiTietToaThuoc, NguoiDung, ToaThuoc, HoaDon
from control_db import create_procedure

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
    err_msg = None
    if request.method == "POST":
        name = request.form["name"]
        gmail = request.form["email"]
        password = request.form["password"]
        confirm = request.form["confirm"]

        if password != confirm:
            err_msg = "Xác nhận mật khẩu không khớp!"
            return render_template("register.html", err_msg=err_msg)
        else:
            existing_user = TaiKhoan.query.filter(TaiKhoan.Email == gmail).first()
            if existing_user:
                err_msg = "Tài khoản này đã được đăng ký"
                return render_template("register.html", err_msg=err_msg)
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
                    err_msg = "Đăng ký thành công! Vui lòng đăng nhập để tiếp tục!"
                    return redirect('/login',err_msg=err_msg)
                except:
                    db.session.rollback()
                    err_msg = "Hệ thống đã bị lỗi! Xin vui lòng thử lại sau"
    return render_template("register.html", err_msg=err_msg)


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
                return redirect('/admin')
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


@app.route("/treatment/create", methods=["GET", "POST"])
def create_treatment():
    username = current_user.nguoi_dung.HoVaTen
    den_cus = dao.load_khach_hang_with_nha_si(current_user.id)
    if request.method == "POST":
        nha_si_id = current_user.id
        khach_hang_id = request.form.get("customer_id")
        chan_doan = request.form.get("diagnosis")

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


@app.route("/treatment/detail/<int:phieu_id>", methods=["GET", "POST"])
def treatment_detail(phieu_id):
    phieu = PhieuDieuTri.query.get_or_404(phieu_id)

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
                new_detail = ChiTietPhieuDieuTri(
                    PhieuDieuTriId=phieu.id,
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

        return redirect(url_for('treatment_detail', phieu_id=phieu_id))

    ds_dich_vu = DichVu.query.all()

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

    return redirect(url_for('treatment_detail', phieu_id=phieu_id))


@app.route("/medicine")
@app.route("/medicine/<int:phieu_id>")
def medicine_page(phieu_id=None):
    if phieu_id is None:
        ds_phieu = PhieuDieuTri.query.outerjoin(HoaDon).filter(
            or_(
                HoaDon.id == None,
                HoaDon.DaThanhToan == False
            )
        ).order_by(PhieuDieuTri.id.desc()).all()

        return render_template("medicine.html",
                               ds_phieu=ds_phieu,
                               mode="select")

    toa_thuoc = ToaThuoc.query.filter_by(PhieuDieuTriId=phieu_id).first()
    if not toa_thuoc:
        toa_thuoc = ToaThuoc(PhieuDieuTriId=phieu_id)
        db.session.add(toa_thuoc)
        db.session.commit()

    medicines_data = dao.get_available_medicines()

    return render_template("medicine.html",
                           toa_thuoc=toa_thuoc,
                           medicines=medicines_data,
                           mode="detail")


@app.route("/medicine/add", methods=["POST"])
def medicine_add():
    try:
        toa_thuoc_id = request.form.get("toa_thuoc_id")
        current_toa = dao.get_toa_thuoc_by_id(toa_thuoc_id)
        thuoc_id = int(request.form.get("thuoc_id"))
        lieu_dung = float(request.form.get("lieu_dung"))
        so_ngay = int(request.form.get("so_ngay"))
        ghi_chu = request.form.get("ghi_chu")

        so_luong_moi = int(math.ceil(lieu_dung * so_ngay))

        existing_item = ChiTietToaThuoc.query.filter_by(
            ToaThuocId=toa_thuoc_id,
            ThuocId=thuoc_id
        ).first()

        so_luong_da_ke = existing_item.SoLuong if existing_item else 0

        available_list = dao.get_available_medicines()
        selected_med = next((item for item in available_list if item[0].id == thuoc_id), None)


        if not selected_med:
            return "Thuốc không hợp lệ", 400

        real_stock = selected_med.total_stock

        total_request = so_luong_da_ke + so_luong_moi

        if total_request > real_stock:
            flash(f"Kho chỉ còn {real_stock}. Trong toa đã có {so_luong_da_ke}, thêm {so_luong_moi} nữa là quá tải!",
                  "error")
            return redirect(url_for('medicine_page'))

        if existing_item:
            existing_item.SoLuong += so_luong_moi
            existing_item.ThanhTien = existing_item.SoLuong * selected_med[0].GiaBan
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

        return redirect(url_for('medicine_page',phieu_id=current_toa.PhieuDieuTriId))
    except Exception as e:
        print(e)
        return "Lỗi xóa", 500

@app.route("/medicine/save", methods=["POST"])
def medicine_save():
    try:
        toa_thuoc_id = request.form.get("toa_thuoc_id")

        toa_thuoc = ToaThuoc.query.get(int(toa_thuoc_id))
        if not toa_thuoc:
            return "Lỗi: Không tìm thấy toa thuốc", 404

        details = toa_thuoc.ds_chi_tiet_thuoc
        for item in details:
            stock_ok = dao.deduct_stock_fifo(item.ThuocId, item.SoLuong)
            if not stock_ok:
                db.session.rollback()
                flash(f"Lỗi: Thuốc {item.loai_thuoc.TenThuoc} không đủ tồn kho!", "danger")
                return redirect(url_for('medicine_page', phieu_id=toa_thuoc.PhieuDieuTriId))

        dao.create_draft_invoice(toa_thuoc.PhieuDieuTriId)

        db.session.commit()

        flash("Đã lưu toa thuốc và chuyển sang bộ phận thu ngân!", "success")

        return redirect(url_for('dashboard'))

    except Exception as e:
        db.session.rollback()
        print(f"Lỗi: {e}")
        flash("Có lỗi xảy ra khi lưu toa thuốc.", "danger")
        return redirect(request.referrer)


@app.route("/MakeAppointment", methods=["GET", "POST"])
def appointment():
    if request.method == "POST":
        name = request.form.get("name")
        day_str = request.form.get("day")
        time_str = request.form.get("time")
        dentist_id = int(request.form.get("dentist"))
        service_id = int(request.form.get("service"))

        day = datetime.strptime(day_str, "%Y-%m-%d").date()
        time = datetime.strptime(time_str, "%H:%M").time()

        lich_trung = LichKham.query.filter(
            LichKham.NhaSiId == dentist_id,
            func.date(LichKham.NgayKham) == day,
            func.time(LichKham.GioKham) == time
        ).first()

        if lich_trung:
            flash(f"Bác sĩ đã có lịch hẹn vào lúc {time} ngày {day}. Vui lòng chọn giờ khác!", "danger")
            return redirect("/MakeAppointment")

        else:
            try:
                sql = text("CALL ThemLichKham(:MaNhaSi, :NgayKham, :GioKham, :MaKhachHang, :MaDichVu)")
                db.session.execute(sql, {
                    "MaNhaSi": dentist_id,
                    "NgayKham": day,
                    "GioKham": time,
                    "MaKhachHang": current_user.id,
                    "MaDichVu": service_id
                })
                db.session.commit()

                flash("Đặt lịch thành công!", "success")
                return redirect('/MakeAppointment')

            except Exception as e:
                db.session.rollback()
                if hasattr(e.orig, 'args') and len(e.orig.args) > 1:
                    msg = e.orig.args[1]
                    msg = msg.lstrip(". ").strip()
                    flash(msg, "danger")
                else:
                    flash("Bác sĩ bạn chọn đã đủ lịch khám trong ngày.", "danger")
                return redirect("/MakeAppointment")

    return render_template("MakeAppointment.html")


@login.user_loader
def get_user(user_id):
    return dao.get_user_by_id(user_id)


@app.route("/cashier", methods=["GET", "POST"])
@login_required
def cashier_page():
    unpaid_bills = dao.get_unpaid_bills()
    bill_details = None

    if request.method == "POST":
        action = request.form.get("action")
        phieu_id = request.form.get("phieu_id")

        if phieu_id:
            bill_details = dao.get_bill_details(phieu_id)

            if action == "pay" and bill_details:
                try:
                    ke_toan_id = current_user.NguoiDungId

                    dao.save_payment(
                        phieu_id=phieu_id,
                        tong_tien=bill_details['tong_cong'],
                        ke_toan_id=ke_toan_id
                    )

                    flash("Thanh toán thành công!", "success")
                    return redirect(url_for('cashier_page'))

                except Exception as e:
                    db.session.rollback()
                    print(e)
                    flash("Lỗi hệ thống: " + str(e), "error")

    if request.method == "POST" and request.form.get("phieu_id"):
        bill_details = dao.get_bill_details(request.form.get("phieu_id"))

    return render_template("cashier.html", unpaid_bills=unpaid_bills, bill=bill_details)
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

    user.nguoi_dung.HoVaTen = request.form.get("HoVaTen")
    user.nguoi_dung.GioiTinh = request.form.get("GioiTinh")
    ngay_sinh = request.form.get("NgaySinh")
    if ngay_sinh:
        user.nguoi_dung.NgaySinh = datetime.strptime(ngay_sinh, "%Y-%m-%d").date()
    user.nguoi_dung.SDT = request.form.get("SDT")

    avatar_file = request.files.get("Avatar")
    if avatar_file and avatar_file.filename != "":
        filename = secure_filename(avatar_file.filename)
        avatar_path = os.path.join("static", "uploads", filename)
        avatar_file.save(avatar_path)
        user.Avatar = "/" + avatar_path.replace("\\", "/")

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

    total_doctors = NhaSi.query.filter_by(active=True).count()
    total_patients = KhachHang.query.filter_by(active=True).count()
    total_accountants = KeToan.query.filter_by(active=True).count()

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

    bills_today = PhieuDieuTri.query.filter(PhieuDieuTri.created_date == today).count()
    bills_week = PhieuDieuTri.query.filter(
        extract('week', PhieuDieuTri.created_date) == week_num,
        extract('year', PhieuDieuTri.created_date) == today.year
    ).count()
    bills_month = PhieuDieuTri.query.filter(
        extract('month', PhieuDieuTri.created_date) == today.month,
        extract('year', PhieuDieuTri.created_date) == today.year
    ).count()

    popular_services = db.session.query(
        DichVu.TenDichVu, func.count(ChiTietPhieuDieuTri.DichVuId)
    ).join(ChiTietPhieuDieuTri, ChiTietPhieuDieuTri.DichVuId == DichVu.id) \
        .group_by(DichVu.TenDichVu) \
        .order_by(func.count(ChiTietPhieuDieuTri.DichVuId).desc()).limit(10).all()

    top_medicines = db.session.query(
        Thuoc.TenThuoc, func.sum(ChiTietToaThuoc.SoLuong)
    ).join(ChiTietToaThuoc, ChiTietToaThuoc.ThuocId == Thuoc.id) \
        .group_by(Thuoc.TenThuoc) \
        .order_by(func.sum(ChiTietToaThuoc.SoLuong).desc()).limit(10).all()

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


@app.route("/admin/api/revenue-chart", methods=["POST"])
@login_required
def get_revenue_chart_data():
    if current_user.Role != UserRole.ADMIN:
        return jsonify({"error": "Unauthorized"}), 403

    filter_type = request.form.get("filter")
    labels = []
    data = []
    label_text = ""
    current_year = datetime.now().year

    try:
        if filter_type == "doctor":
            results = db.session.query(
                NhaSi.HoVaTen,
                func.sum(ChiTietPhieuDieuTri.SoLuong * DichVu.ChiPhi)
            ).join(PhieuDieuTri, PhieuDieuTri.NhaSiId == NhaSi.id) \
                .join(ChiTietPhieuDieuTri, ChiTietPhieuDieuTri.PhieuDieuTriId == PhieuDieuTri.id) \
                .join(DichVu, ChiTietPhieuDieuTri.DichVuId == DichVu.id) \
                .group_by(NhaSi.HoVaTen).all()

            label_text = "Doanh thu theo Bác sĩ (Dịch vụ)"
            for row in results:
                name = row[0] if row[0] else "Unknown"
                total = float(row[1]) if row[1] else 0
                labels.append(name)
                data.append(total)

        elif filter_type == "month":
            results = db.session.query(
                extract('month', PhieuDieuTri.created_date).label('thang'),
                func.sum(ChiTietPhieuDieuTri.SoLuong * DichVu.ChiPhi)
            ).join(ChiTietPhieuDieuTri, ChiTietPhieuDieuTri.PhieuDieuTriId == PhieuDieuTri.id) \
                .join(DichVu, ChiTietPhieuDieuTri.DichVuId == DichVu.id) \
                .filter(extract('year', PhieuDieuTri.created_date) == current_year) \
                .group_by(extract('month', PhieuDieuTri.created_date)) \
                .order_by(extract('month', PhieuDieuTri.created_date)).all()

            label_text = f"Doanh thu theo Tháng (Năm {current_year})"

            revenue_by_month = {m: 0 for m in range(1, 13)}

            for row in results:
                month = int(row[0])
                total = float(row[1])
                revenue_by_month[month] = total

            labels = [f"Tháng {m}" for m in range(1, 13)]
            data = [revenue_by_month[m] for m in range(1, 13)]

        return jsonify({
            "labels": labels,
            "data": data,
            "label_text": label_text
        })
    except Exception as e:
        print("Lỗi API Biểu đồ:", e)
        return jsonify({"error": str(e)}), 500
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

    hoten = request.form.get("hoten")
    email = request.form.get("email")
    password = request.form.get("password")
    role = request.form.get("role")

    if TaiKhoan.query.filter_by(Email=email).first():
        flash("Email đã tồn tại!", "danger")
        return redirect("/admin/accounts")

    nguoidung = NguoiDung(HoVaTen=hoten)

    hashed = hashlib.md5(password.encode("utf-8")).hexdigest()

    tk = TaiKhoan(
        Email=email,
        MatKhau=hashed,
        Role=UserRole[role],
        nguoi_dung=nguoidung
    )

    try:
        db.session.add(nguoidung)
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

with app.app_context():
    db.create_all()
    create_procedure()

if __name__ == "__main__":
    app.run(debug=True)
