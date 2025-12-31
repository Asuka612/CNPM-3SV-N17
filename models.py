import enum
import hashlib
from datetime import datetime
from flask import json
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, DateTime, Time, Enum, Boolean
from sqlalchemy.orm import relationship
from __init__ import app, db

# ================= ENUMS =================
class UserRole(enum.Enum):
    ADMIN = "ADMIN"
    KHACHHANG = "KHACHHANG"
    NHASI = "NHASI"
    KETOAN = "KETOAN"

class GioiTinh(enum.Enum):
    NAM = "NAM"
    NU = "NU"
    KHAC = "KHAC"

# ================= BASE MODEL =================
class Base(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, default=datetime.now)
    active =  Column(Boolean, default=True)

# ================= USER & ACCOUNT SYSTEM =================
class NguoiDung(Base):
    __tablename__ = 'NguoiDung'

    HoVaTen = Column(String(200), nullable=False)
    NgaySinh = Column(Date, nullable=True)
    GioiTinh = Column(Enum(GioiTinh),default=GioiTinh.NAM, nullable=True)
    SDT = Column(String(15), nullable=True)
    type = Column(String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'nguoidung',
        'polymorphic_on': type
    }

    def __str__(self):
        return self.HoVaTen

class NhaSi(NguoiDung):
    __tablename__ = 'NhaSi'

    id = Column(Integer, ForeignKey('NguoiDung.id'), primary_key=True)
    MaNhaSi = Column(String(20), unique=True)
    ChuyenMonId = Column(Integer, ForeignKey('ChuyenMon.id'))

    chuyen_mon = relationship('ChuyenMon', backref='ds_nha_si', lazy=True)

    __mapper_args__ = {
        'polymorphic_identity': 'nhasi',
    }

class KhachHang(NguoiDung):
    __tablename__ = 'KhachHang'

    id = Column(Integer, ForeignKey('NguoiDung.id'), primary_key=True)
    TienSuBenhLy = Column(String(250))

    __mapper_args__ = {
        'polymorphic_identity': 'khachhang',
    }

class KeToan(NguoiDung):
    __tablename__ = 'KeToan'

    id = Column(Integer, ForeignKey('NguoiDung.id'), primary_key=True)
    ChungChiHanhNghe = Column(String(250))

    __mapper_args__ = {
        'polymorphic_identity': 'ketoan',
    }

class Admin(NguoiDung):
    __tablename__ = 'Admin'

    id = Column(Integer, ForeignKey('NguoiDung.id'), primary_key=True)
    CapDoQuanTri = Column(Integer, default=1)

    __mapper_args__ = {
        'polymorphic_identity': 'admin',
    }

class TaiKhoan(Base, UserMixin):
    __tablename__ = 'TaiKhoan'

    NguoiDungId = Column(Integer, ForeignKey('NguoiDung.id'), unique=True, nullable=False)
    Email = Column(String(100), unique=True)
    MatKhau = Column(String(255), nullable=False)
    Avatar = Column(String(300), default='https://cdn-icons-png.flaticon.com/128/18388/18388709.png')
    Role = Column(Enum(UserRole), default=UserRole.KHACHHANG,nullable=False)

    nguoi_dung = relationship('NguoiDung', backref='tai_khoan', uselist=False, lazy=True)


# ================= SPECIALIZATION =================
class ChuyenMon(Base):
    __tablename__ = 'ChuyenMon'
    TenChuyenMon = Column(String(150), nullable=False)
    MoTa = Column(String(255))

# ================= CLINIC OPERATIONS =================
class LichKham(Base):
    __tablename__ = 'LichKham'

    NhaSiId = Column(Integer, ForeignKey('NhaSi.id'), nullable=False)
    KhachHangId = Column(Integer, ForeignKey('KhachHang.id'), nullable=False)
    DichVuId = Column(Integer, ForeignKey('DichVu.id'), nullable=False)
    NgayKham = Column(Date)
    GioKham = Column(Time)

    benh_nhan = relationship('KhachHang', backref='ds_lich_kham', lazy=True)

class DichVu(Base):
    __tablename__ = 'DichVu'

    TenDichVu = Column(String(150), nullable=False)
    ChiPhi = Column(Float, default=0.0)
    MoTa = Column(String(250))

    def __str__(self):
        return self.TenDichVu

class PhieuDieuTri(Base):
    __tablename__ = 'PhieuDieuTri'

    KhachHangId = Column(Integer, ForeignKey('KhachHang.id'), nullable=False)
    NhaSiId = Column(Integer, ForeignKey('NhaSi.id'), nullable=False)
    ChuanDoan = Column(String(250))

    toa_thuoc = relationship('ToaThuoc', backref='phieu_dieu_tri', uselist=False, lazy=True)
    khach_hang = relationship('KhachHang', backref='ds_phieu_dieu_tri', uselist=False, lazy=True)

class ChiTietPhieuDieuTri(db.Model):
    __tablename__ = 'ChiTietPhieuDieuTri'

    PhieuDieuTriId = Column(Integer, ForeignKey('PhieuDieuTri.id'), primary_key=True, nullable=False)
    DichVuId = Column(Integer, ForeignKey('DichVu.id'), primary_key=True, nullable=False)
    SoLuong = Column(Integer, default=1)
    GhiChu = Column(String(255))

    dich_vu = relationship('DichVu', backref='cac_lan_su_dung',lazy=True)
    phieu_dieu_tri = relationship('PhieuDieuTri', backref='ds_chi_tiet')

class Thuoc(Base):
    __tablename__ = 'Thuoc'

    TenThuoc = Column(String(150), nullable=False)
    DonVi = Column(String(20))
    GiaBan = Column(Float, default=0.0)

    lo_thuoc = relationship('LoThuoc', backref='loai_thuoc', lazy=True)

class LoThuoc(db.Model):
    __tablename__ = 'LoThuoc'

    MaLoThuoc = Column(String(150), primary_key=True, nullable=False)
    ThuocId = Column(Integer, ForeignKey('Thuoc.id'), nullable=False)
    SoLuongNhap = Column(Integer)
    SoLuongTon = Column(Integer)
    HanSuDung = Column(Date)
    active =  Column(Boolean, default=True)


class ToaThuoc(Base):
    __tablename__ = 'ToaThuoc'

    PhieuDieuTriId = Column(Integer, ForeignKey('PhieuDieuTri.id'), nullable=False)

    ds_chi_tiet_thuoc = relationship('ChiTietToaThuoc', backref='toa_thuoc', lazy=True)

class ChiTietToaThuoc(db.Model):
    __tablename__ = 'ChiTietToaThuoc'

    ToaThuocId = Column(Integer, ForeignKey('ToaThuoc.id'), nullable=False, primary_key=True)
    ThuocId = Column(Integer, ForeignKey('Thuoc.id'), nullable=False, primary_key=True)

    SoLuong = Column(Integer,nullable=False)
    LieuDung = Column(Float, nullable=False)
    SoNgay = Column(Integer, nullable=False)
    GhiChu = Column(String(255))
    ThanhTien = Column(Float, default=0.0)

    loai_thuoc = relationship('Thuoc', backref='ds_thuoc', lazy=True)


# ================= BILLING (BẢNG MỚI QUAN TRỌNG) =================
class HoaDon(Base):
    __tablename__ = 'HoaDon'

    PhieuDieuTriId = Column(Integer, ForeignKey('PhieuDieuTri.id'), unique=True, nullable=False)
    KeToanId = Column(Integer, ForeignKey('KeToan.id'), nullable=True)
    TongTien = Column(Float, default=0.0)
    DaThanhToan = Column(Boolean, default=False)

    phieu_dieu_tri = relationship('PhieuDieuTri', backref='hoa_don', uselist=False)


# ================= MAIN RUN =================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # with open("data/ChuyenMon.json", encoding="utf-8") as f:
        #     products = json.load(f)
        #     for p in products:
        #         db.session.add(ChuyenMon(**p))
        #
        # with open("data/DichVu.json", encoding="utf-8") as f:
        #     products = json.load(f)
        #     for p in products:
        #         db.session.add(DichVu(**p))
        #
        # with open("data/Thuoc.json", encoding="utf-8") as f:
        #     products = json.load(f)
        #     for p in products:
        #         db.session.add(Thuoc(**p))
        #
        # with open("data/Admin.json", encoding="utf-8") as f:
        #     products = json.load(f)
        #     for p in products:
        #         db.session.add(Admin(**p))
        #
        # with open("data/KeToan.json", encoding="utf-8") as f:
        #     products = json.load(f)
        #     for p in products:
        #         db.session.add(KeToan(**p))
        #
        # with open("data/KhachHang.json", encoding="utf-8") as f:
        #     products = json.load(f)
        #     for p in products:
        #         db.session.add(KhachHang(**p))
        #
        # with open("data/NhaSi.json", encoding="utf-8") as f:
        #     products = json.load(f)
        #     for p in products:
        #         db.session.add(NhaSi(**p))
        #
        # with open("data/TaiKhoan.json", encoding="utf-8") as f:
        #     products = json.load(f)
        #     for p in products:
        #         db.session.add(TaiKhoan(**p))
        #
        # with open("data/PhieuDieuTri.json", encoding="utf-8") as f:
        #     products = json.load(f)
        #     for p in products:
        #         db.session.add(PhieuDieuTri(**p))
        #
        # with open("data/LichKham.json", encoding="utf-8") as f:
        #     products = json.load(f)
        #     for p in products:
        #         db.session.add(LichKham(**p))
        #
        # with open("data/LoThuoc.json", encoding="utf-8") as f:
        #     products = json.load(f)
        #     for p in products:
        #         db.session.add(LoThuoc(**p))
        #
        # with open("data/ToaThuoc.json", encoding="utf-8") as f:
        #     products = json.load(f)
        #     for p in products:
        #         db.session.add(ToaThuoc(**p))
        #
        # with open("data/HoaDon.json", encoding="utf-8") as f:
        #     products = json.load(f)
        #     for p in products:
        #         db.session.add(HoaDon(**p))
        #
        # with open("data/ChiTietPhieuDieuTri.json", encoding="utf-8") as f:
        #     products = json.load(f)
        #     for p in products:
        #         db.session.add(ChiTietPhieuDieuTri(**p))
        #
        # with open("data/ChiTietToaThuoc.json", encoding="utf-8") as f:
        #     products = json.load(f)
        #     for p in products:
        #         db.session.add(ChiTietToaThuoc(**p))

        db.session.commit()
