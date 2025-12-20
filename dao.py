import hashlib
import json
from click import password_option
from __init__ import app
from models import TaiKhoan, NguoiDung, NhaSi , DichVu, Thuoc
from __init__ import app, db

def load_nhasi():
    return db.session.query(NhaSi).all()

def auth_user(gmail, password):
    password = hashlib.md5(password.encode("utf-8")).hexdigest()
    return TaiKhoan.query.filter(TaiKhoan.Email.__eq__(gmail), TaiKhoan.MatKhau.__eq__(password)).first()

def get_user_by_id(user_id):
    return TaiKhoan.query.get(user_id)

def load_dich_vu():
    return DichVu.query.all()

def load_thuoc():
    return Thuoc.query.all()

if __name__=="__main__":
    with app.app_context():
        print(load_nhasi())
