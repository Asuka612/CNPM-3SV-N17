import json

from __init__ import db, app
from sqlalchemy import Column, Integer, Float, String, ForeignKey, Text, DateTime, Enum, Boolean
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


# class Category(Base):
#     products = relationship('Product', backref="category", lazy=True)

# class Product(Base):
#     image = Column(String(500),
#                    default="https://e7.pngegg.com/pngimages/10/205/png-clipart-computer-icons-error-information-error-angle-triangle-thumbnail.png")
#     price = Column(Float, default=0.0)
#     cate_id = Column(Integer, ForeignKey(Category.id), nullable=False)
#     description = Column(Text)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        # c1 = Category(name="Laptop")
        # c2 = Category(name="Mobile")
        # c3 = Category(name="Tablet")
        #
        # db.session.add_all([c1, c2, c3])
        #
        # with open("saleApp/data/product.json", encoding="utf-8") as f:
        #     products = json.load(f)
        #
        #     for p in products:
        #         db.session.add(Product(**p))
        import hashlib
        password = hashlib.md5("123".encode("utf-8")).hexdigest()
        u1 = User(name="Khoa", gmail = "tp281973555k@gmail.com", password =password, role=UserRole.USER)

        db.session.add(u1)

        db.session.commit()
