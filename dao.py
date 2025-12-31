import hashlib
import json
import pdb

from click import password_option
from sqlalchemy import func, or_
from datetime import datetime, timedelta
from __init__ import app
from models import TaiKhoan, NguoiDung, NhaSi, DichVu, Thuoc, KhachHang, LichKham, UserRole, LoThuoc, ToaThuoc, \
    PhieuDieuTri, HoaDon
from __init__ import app, db, cache
from sqlalchemy.orm import joinedload


@cache.cached(timeout=111600, key_prefix='all_dentists')
def load_nhasi():
    return db.session.query(NhaSi).all()


@cache.cached(timeout=111600, key_prefix='all_customers')
def load_nguoi_dung():
    return TaiKhoan.query.options(joinedload(TaiKhoan.nguoi_dung)) \
        .filter(TaiKhoan.Role == UserRole.KHACHHANG) \
        .all()


@cache.cached(timeout=111600, key_prefix='all_services')
def load_dich_vu():
    return DichVu.query.all()


@cache.cached(timeout=111600, key_prefix='all_medicines')
def load_thuoc():
    return Thuoc.query.all()


def get_toa_thuoc_by_id(toa_thuoc_id):
    try:
        return db.session.get(ToaThuoc, int(toa_thuoc_id))
    except Exception:
        return None


def cleanup_expired_batches():

    limit_date = datetime.now().date() + timedelta(days=10)

    bad_batches = LoThuoc.query.filter(
        LoThuoc.active == True,
        LoThuoc.HanSuDung < limit_date
    ).all()

    count = 0
    for batch in bad_batches:
        batch.active = False
        count += 1

    if count > 0:
        db.session.commit()
        print(f"Đã tự động khóa {count} lô thuốc sắp hết hạn.")


def get_available_medicines():

    cleanup_expired_batches()

    medicines = db.session.query(
        Thuoc,
        func.sum(LoThuoc.SoLuongTon).label('total_stock')
    ).join(LoThuoc) \
        .filter(LoThuoc.active == True) \
        .group_by(Thuoc.id) \
        .having(func.sum(LoThuoc.SoLuongTon) > 0) \
        .all()

    return medicines


def deduct_stock_fifo(thuoc_id, quantity_needed):
    """
    Trừ kho FIFO.
    Lưu ý: Không gọi db.session.commit() ở đây để app.py quản lý transaction lớn.
    """
    batches = LoThuoc.query.filter(
        LoThuoc.ThuocId == thuoc_id,
        LoThuoc.active == True,
        LoThuoc.SoLuongTon > 0
    ).order_by(LoThuoc.HanSuDung.asc()).all()

    remaining = quantity_needed
    for batch in batches:
        if remaining <= 0: break

        if batch.SoLuongTon >= remaining:
            batch.SoLuongTon -= remaining
            remaining = 0
        else:
            remaining -= batch.SoLuongTon
            batch.SoLuongTon = 0

    if remaining == 0:
        return True
    else:
        return False


@cache.memoize(timeout=300)
def load_khach_hang_with_nha_si(nha_si_id):
    return KhachHang.query.filter(KhachHang.ds_lich_kham.any(NhaSiId=nha_si_id)).all()


def get_unpaid_bills():
    """
    Lấy danh sách phiếu điều trị cần thanh toán, bao gồm:
    1. Phiếu chưa có record trong bảng HoaDon (HoaDon.id is NULL).
    2. Phiếu đã có HoaDon nhưng DaThanhToan = False.
    """
    return db.session.query(PhieuDieuTri) \
        .outerjoin(HoaDon, PhieuDieuTri.id == HoaDon.PhieuDieuTriId) \
        .filter(
        or_(
            HoaDon.id == None,
            HoaDon.DaThanhToan == False
        )
    ).all()


def save_payment(phieu_id, tong_tien, ke_toan_id):
    """
    Lưu thanh toán và cập nhật ID kế toán thực hiện.
    """
    invoice = HoaDon.query.filter_by(PhieuDieuTriId=phieu_id).first()

    if invoice:
        invoice.DaThanhToan = True
        invoice.TongTien = tong_tien
        invoice.KeToanId = ke_toan_id
    else:
        new_invoice = HoaDon(
            PhieuDieuTriId=phieu_id,
            TongTien=tong_tien,
            DaThanhToan=True,
            KeToanId=ke_toan_id
        )
        db.session.add(new_invoice)

    db.session.commit()
    return True


def get_bill_details(phieu_id):
    """
    Tính toán chi tiết tiền nong cho 1 phiếu điều trị
    """
    phieu = PhieuDieuTri.query.get(int(phieu_id))
    if not phieu:
        return None

    services = []
    total_service_cost = 0

    for ct in phieu.ds_chi_tiet:
        thanh_tien = ct.SoLuong * ct.dich_vu.ChiPhi
        total_service_cost += thanh_tien

        services.append({
            "ten_dich_vu": ct.dich_vu.TenDichVu,
            "so_luong": ct.SoLuong,
            "don_gia": ct.dich_vu.ChiPhi,
            "thanh_tien": thanh_tien
        })

    medicines = []
    total_medicine_cost = 0

    hoa_don = HoaDon.query.filter_by(PhieuDieuTriId=phieu.id).first()
    da_thanh_toan = hoa_don.DaThanhToan if hoa_don else False

    if phieu.toa_thuoc:
        for ct_thuoc in phieu.toa_thuoc.ds_chi_tiet_thuoc:
            total_medicine_cost += ct_thuoc.ThanhTien

            medicines.append({
                "ten_thuoc": ct_thuoc.loai_thuoc.TenThuoc,
                "so_luong": ct_thuoc.SoLuong,
                "don_gia": ct_thuoc.loai_thuoc.GiaBan,
                "thanh_tien": ct_thuoc.ThanhTien
            })

    return {
        "phieu_id": phieu.id,
        "ten_khach_hang": phieu.khach_hang.HoVaTen,
        "ngay_tao": phieu.created_date,
        "list_dich_vu": services,
        "list_thuoc": medicines,
        "tong_tien_dv": total_service_cost,
        "tong_tien_thuoc": total_medicine_cost,
        "tong_cong": total_service_cost + total_medicine_cost,
        "da_thanh_toan": da_thanh_toan
    }


def create_draft_invoice(phieu_id):
    """
    Hàm này tính tổng tiền (Dịch vụ + Thuốc) và tạo hóa đơn trạng thái CHƯA THANH TOÁN.
    """
    phieu = PhieuDieuTri.query.get(phieu_id)
    if not phieu:
        return False

    tong_tien_dv = 0
    for ct in phieu.ds_chi_tiet:
        tong_tien_dv += ct.SoLuong * ct.dich_vu.ChiPhi

    tong_tien_thuoc = 0
    if phieu.toa_thuoc:
        for ct_thuoc in phieu.toa_thuoc.ds_chi_tiet_thuoc:
            tong_tien_thuoc += ct_thuoc.ThanhTien

    tong_cong = tong_tien_dv + tong_tien_thuoc

    hoa_don = HoaDon.query.filter_by(PhieuDieuTriId=phieu_id).first()

    if hoa_don:
        hoa_don.TongTien = tong_cong
    else:
        new_invoice = HoaDon(
            PhieuDieuTriId=phieu_id,
            TongTien=tong_cong,
            DaThanhToan=False,
            KeToanId=None
        )
        db.session.add(new_invoice)
    return True


def auth_user(gmail, password):
    password = hashlib.md5(password.encode("utf-8")).hexdigest()
    return TaiKhoan.query.filter(TaiKhoan.Email.__eq__(gmail), TaiKhoan.MatKhau.__eq__(password)).first()


def get_user_by_id(user_id):
    return TaiKhoan.query.get(user_id)


if __name__ == "__main__":
    with app.app_context():
        print(get_unpaid_bills())
