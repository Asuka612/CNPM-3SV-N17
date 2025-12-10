import json
import hashlib

from __init__ import db, app
from sqlalchemy import Column, Integer, Float, String, ForeignKey, Text, DateTime, Enum, Boolean, Date, Time
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as RoleEnum
from flask_login import UserMixin

class Base(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.now())
    active = Column(Boolean, default=True)

    def __str__(self):
        return self.name

class UserRole(RoleEnum):
    USER = 1
    ADMIN = 2

class User(Base, UserMixin):
    gmail = Column(String(150), unique=True, nullable=False)
    password = Column(String(150), nullable=False)
    avatar = Column(String(300),
                    default='https://cdn-icons-png.flaticon.com/128/18388/18388709.png')
    role = Column(Enum(UserRole),default=UserRole.USER)

# ---------------------<<FAKE DATA NHA KHOA>>---------------------
class ChuyenMon(db.Model):
    __tablename__ = 'ChuyenMon'
    MaChuyenMon = Column(String(10), primary_key=True)
    TenChuyenMon = Column(String(100), nullable=False)
    MoTa = Column(String(255))

    NhaSi = relationship('NhaSi', backref='ChuyenMon', lazy=True)
    KeToan = relationship('KeToan', backref='ChuyenMon', lazy=True)


class NguoiDung(db.Model):
    __tablename__ = 'NguoiDung'
    MaNguoiDung = Column(String(10), primary_key=True)
    Ho = Column(String(50), nullable=False)
    Ten = Column(String(50), nullable=False)
    NgaySinh = Column(Date, nullable=False)
    GioiTinh = Column(String(1), nullable=False)
    SDT = Column(String(15))

    NhaSi = relationship('NhaSi', backref='NguoiDung', lazy=True)
    KhachHang = relationship('KhachHang', backref='NguoiDung', lazy=True)
    KeToan = relationship('KeToan', backref='NguoiDung', lazy=True)
    TaiKhoan = relationship('TaiKhoan', backref='NguoiDung', lazy=True)


class NhaSi(db.Model):
    __tablename__ = 'NhaSi'
    MaNhaSi = Column(String(10), ForeignKey('NguoiDung.MaNguoiDung'), primary_key=True)
    MaChuyenMon = Column(String(10), ForeignKey('ChuyenMon.MaChuyenMon'))
    NgayNhanViec = Column(Date)
    Email = Column(String(100))

    LichKham = relationship('LichKham', backref='NhaSi', lazy=True)
    PhieuDieuTri = relationship('PhieuDieuTri', backref='NhaSi', lazy=True)
    ToaThuoc = relationship('ToaThuoc', backref='NhaSi', lazy=True)


class KhachHang(db.Model):
    __tablename__ = 'KhachHang'
    MaKhachHang = Column(String(10), ForeignKey('NguoiDung.MaNguoiDung'), primary_key=True)
    DiaChi = Column(String(255))

    LichKham = relationship('LichKham', backref='KhachHang', lazy=True)
    PhieuDieuTri = relationship('PhieuDieuTri', backref='KhachHang', lazy=True)


class KeToan(db.Model):
    __tablename__ = 'KeToan'
    MaKeToan = Column(String(10), ForeignKey('NguoiDung.MaNguoiDung'), primary_key=True)
    MaChuyenMon = Column(String(10), ForeignKey('ChuyenMon.MaChuyenMon'))
    NgayNhanViec = Column(Date)


class TaiKhoan(db.Model):
    __tablename__ = 'TaiKhoan'
    MaTaiKhoan = Column(String(10), primary_key=True)
    MaNguoiDung = Column(String(10), ForeignKey('NguoiDung.MaNguoiDung'))
    TenDangNhap = Column(String(50), unique=True, nullable=False)
    MatKhau = Column(String(100), nullable=False)


class DichVu(db.Model):
    __tablename__ = 'DichVu'
    MaDichVu = Column(String(10), primary_key=True)
    TenDichVu = Column(String(100), nullable=False)
    ChiPhi = Column(Integer, nullable=False)
    MoTa = Column(String(255))

    ChiTietPhieuDieuTri = relationship('ChiTietPhieuDieuTri', backref='DichVu', lazy=True)


class Thuoc(db.Model):
    __tablename__ = 'Thuoc'
    MaThuoc = Column(String(10), primary_key=True)
    TenThuoc = Column(String(100), nullable=False)
    DonVi = Column(String(20))
    MoTa = Column(String(255))

    LoThuoc = relationship('LoThuoc', backref='Thuoc', lazy=True)
    ChiTietLoThuoc = relationship('ChiTietLoThuoc', backref='Thuoc', lazy=True)
    ChiTietToaThuoc = relationship('ChiTietToaThuoc', backref='Thuoc', lazy=True)


class LoThuoc(db.Model):
    __tablename__ = 'LoThuoc'
    MaLoThuoc = Column(String(10), primary_key=True)
    MaThuoc = Column(String(10), ForeignKey('Thuoc.MaThuoc'))
    HanSuDung = Column(Date)

    ChiTietLoThuoc = relationship('ChiTietLoThuoc', backref='LoThuoc', lazy=True)


class ChiTietLoThuoc(db.Model):
    __tablename__ = 'ChiTietLoThuoc'
    MaLoThuoc = Column(String(10), ForeignKey('LoThuoc.MaLoThuoc'), primary_key=True)
    MaThuoc = Column(String(10), ForeignKey('Thuoc.MaThuoc'), primary_key=True)
    SoLuongTon = Column(Integer)


class LichKham(db.Model):
    __tablename__ = 'LichKham'
    MaLichKham = Column(String(10), primary_key=True)
    MaNhaSi = Column(String(10), ForeignKey('NhaSi.MaNhaSi'))
    MaKhachHang = Column(String(10), ForeignKey('KhachHang.MaKhachHang'))
    NgayKham = Column(Date)
    GioKham = Column(Time)


class PhieuDieuTri(db.Model):
    __tablename__ = 'PhieuDieuTri'
    MaPhieuDieuTri = Column(String(10), primary_key=True)
    MaNhaSi = Column(String(10), ForeignKey('NhaSi.MaNhaSi'))
    MaKhachHang = Column(String(10), ForeignKey('KhachHang.MaKhachHang'))
    NgayLap = Column(Date)
    ChuanDoan = Column(String(255))

    ChiTiet = relationship('ChiTietPhieuDieuTri', backref='PhieuDieuTri', lazy=True)
    ToaThuoc = relationship('ToaThuoc', backref='PhieuDieuTri', lazy=True)


class ChiTietPhieuDieuTri(db.Model):
    __tablename__ = 'ChiTietPhieuDieuTri'
    MaPhieuDieuTri = Column(String(10), ForeignKey('PhieuDieuTri.MaPhieuDieuTri'), primary_key=True)
    MaDichVu = Column(String(10), ForeignKey('DichVu.MaDichVu'), primary_key=True)
    GhiChu = Column(String(255))


class ToaThuoc(db.Model):
    __tablename__ = 'ToaThuoc'
    MaToaThuoc = Column(String(10), primary_key=True)
    MaNhaSi = Column(String(10), ForeignKey('NhaSi.MaNhaSi'))
    MaPhieuDieuTri = Column(String(10), ForeignKey('PhieuDieuTri.MaPhieuDieuTri'))
    NgayLap = Column(Date)

    ChiTiet = relationship('ChiTietToaThuoc', backref='ToaThuoc', lazy=True)


class ChiTietToaThuoc(db.Model):
    __tablename__ = 'ChiTietToaThuoc'
    MaToaThuoc = Column(String(10), ForeignKey('ToaThuoc.MaToaThuoc'), primary_key=True)
    MaThuoc = Column(String(10), ForeignKey('Thuoc.MaThuoc'), primary_key=True)
    SoNgayDung = Column(Date)
    SoLuong = Column(Integer)
    DonVi = Column(String(20))
    GhiChu = Column(String(255))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        # ---------------------<<THÊM DATA VÀO CSDL NHA KHOA>>---------------------
        # ChuyenMon
        with open('data/ChuyenMon.json', encoding='utf-8') as f:
            data = json.loads(f.read())
            for v in data:
                db.session.add(ChuyenMon(**v))

        # NguoiDung
        with open('data/NguoiDung.json', encoding='utf-8') as f:
            data = json.loads(f.read())
            for v in data:
                db.session.add(NguoiDung(**v))

        # NhaSi
        with open('data/NhaSi.json', encoding='utf-8') as f:
            data = json.loads(f.read())
            for v in data:
                db.session.add(NhaSi(**v))

        # KhachHang
        with open('data/KhachHang.json', encoding='utf-8') as f:
            data = json.loads(f.read())
            for v in data:
                db.session.add(KhachHang(**v))

        # KeToan
        with open('data/KeToan.json', encoding='utf-8') as f:
            data = json.loads(f.read())
            for v in data:
                db.session.add(KeToan(**v))

        # TaiKhoan
        with open('data/TaiKhoan.json', encoding='utf-8') as f:
            data = json.loads(f.read())
            for v in data:
                db.session.add(TaiKhoan(**v))

        # DichVu
        with open('data/DichVu.json', encoding='utf-8') as f:
            data = json.loads(f.read())
            for v in data:
                db.session.add(DichVu(**v))

        # Thuoc
        with open('data/Thuoc.json', encoding='utf-8') as f:
            data = json.loads(f.read())
            for v in data:
                db.session.add(Thuoc(**v))

        # LoThuoc
        with open('data/LoThuoc.json', encoding='utf-8') as f:
            data = json.loads(f.read())
            for v in data:
                db.session.add(LoThuoc(**v))

        # ChiTietLoThuoc
        with open('data/ChiTietLoThuoc.json', encoding='utf-8') as f:
            data = json.loads(f.read())
            for v in data:
                db.session.add(ChiTietLoThuoc(**v))

        # LichKham
        with open('data/LichKham.json', encoding='utf-8') as f:
            data = json.loads(f.read())
            for v in data:
                db.session.add(LichKham(**v))

        # PhieuDieuTri
        with open('data/PhieuDieuTri.json', encoding='utf-8') as f:
            data = json.loads(f.read())
            for v in data:
                db.session.add(PhieuDieuTri(**v))

        # ChiTietPhieuDieuTri
        with open('data/ChiTietPhieuDieuTri.json', encoding='utf-8') as f:
            data = json.loads(f.read())
            for v in data:
                db.session.add(ChiTietPhieuDieuTri(**v))

        # ToaThuoc
        with open('data/ToaThuoc.json', encoding='utf-8') as f:
            data = json.loads(f.read())
            for v in data:
                db.session.add(ToaThuoc(**v))

        # ChiTietToaThuoc
        with open('data/ChiTietToaThuoc.json', encoding='utf-8') as f:
            data = json.loads(f.read())
            for v in data:
                db.session.add(ChiTietToaThuoc(**v))
        password = hashlib.md5("123".encode("utf-8")).hexdigest()
        u1 = User(name="Khoa", gmail="tp281973555k@gmail.com", password=password, role=UserRole.USER)

        db.session.add(u1)

        password = hashlib.md5("123".encode("utf-8")).hexdigest()
        u1 = User(name="Khoa", gmail="tp281973555k@gmail.com", password=password, role=UserRole.USER)

        db.session.add(u1)

        db.session.commit()
