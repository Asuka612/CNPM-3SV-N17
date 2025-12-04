from flask import Flask, render_template, request, redirect, session, url_for

app = Flask(__name__)
app.secret_key = "secret_key_here"  # cần cho session

# Lưu user tạm thời (giữ để demo, nhưng không bắt buộc)
users = {}

# Trang chủ
@app.route("/")
def home():
    return render_template("home.html")  # home.html bạn đã làm trước

# Đăng ký
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        username = request.form["username"]
        password = request.form["password"]
        confirm = request.form["confirm"]

        if password != confirm:
            return "Xác nhận mật khẩu không khớp!"
        if username in users:
            return "Tài khoản đã tồn tại!"

        users[username] = {"name": name, "email": email, "password": password}
        return redirect("/login")

    return render_template("register.html")

# Đăng nhập (demo nhanh, nhấn login là vào dashboard luôn)
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Lấy tên đăng nhập hoặc mặc định "Khách hàng"
        username = request.form.get("username", "Khách hàng")
        session["user"] = username  # lưu session
        return redirect(url_for("dashboard"))

    return render_template("login.html")

# Dashboard khách hàng
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    username = session["user"]
    # Truyền trực tiếp username, không cần lookup trong users dict
    return render_template("dashboard.html", username=username)

# Logout
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/MakeAppointment.html")
def appointment():
    page = request.args.get("page")
    pages = int(page) if page is not None else 1
    return render_template("MakeAppointment.html", pages=pages)

if __name__ == "__main__":
    app.run(debug=True)
