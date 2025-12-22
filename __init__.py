from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_caching import Cache


app = Flask(__name__)
app.secret_key = "nhungchubetliet=qsrdhuqwh123123ipsdjfg098suf8923u549ihg23wefdhgcyvuiadf6uqwyghryitu32e78y5gui235vgrtf"

app.config["SQLALCHEMY_DATABASE_URI"] ="mysql+pymysql://root:root@localhost/nhakhoadb?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"]=4

app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300

db = SQLAlchemy(app)
login = LoginManager(app)
cache = Cache(app)