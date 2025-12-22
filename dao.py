import hashlib
import json
from click import password_option
from sqlalchemy import func
from datetime import datetime, timedelta
from __init__ import app
from models import TaiKhoan, NguoiDung, NhaSi, DichVu, Thuoc, KhachHang, LichKham, UserRole, LoThuoc, ToaThuoc
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

# --- HÀM 1: TỰ ĐỘNG KHÓA LÔ SẮP HẾT HẠN ---
def cleanup_expired_batches():
    """
    Tìm các lô thuốc active nhưng hạn sử dụng còn dưới 10 ngày so với hiện tại
    Set active = False để không bán nữa.
    """
    # Ngày giới hạn = Hôm nay + 10 ngày
    limit_date = datetime.now().date() + timedelta(days=10)

    # Tìm các lô vi phạm
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


# --- HÀM 2: LẤY DANH SÁCH THUỐC KHẢ DỤNG ---
def get_available_medicines():
    """
    Chỉ lấy thuốc có tổng tồn kho > 0 từ các lô còn active (HSD > 10 ngày)
    """
    # 1. Chạy dọn dẹp trước
    cleanup_expired_batches()

    # 2. Query tính tổng tồn kho của từng thuốc CHỈ TỪ CÁC LÔ ACTIVE
    # Kết quả trả về gồm: (Thuoc Object, TongTonKho)
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

    # Trả về True nếu trừ đủ, False nếu thiếu hàng
    if remaining == 0:
        return True
    else:
        return False


@cache.memoize(timeout=300)
def load_khach_hang_with_nha_si(nha_si_id):
    return KhachHang.query.filter(KhachHang.ds_lich_kham.any(NhaSiId=nha_si_id)).all()

def auth_user(gmail, password):
    password = hashlib.md5(password.encode("utf-8")).hexdigest()
    return TaiKhoan.query.filter(TaiKhoan.Email.__eq__(gmail), TaiKhoan.MatKhau.__eq__(password)).first()

def get_user_by_id(user_id):
    return TaiKhoan.query.get(user_id)

if __name__ == "__main__":
    with app.app_context():
        print(get_toa_thuoc_by_id(1))
