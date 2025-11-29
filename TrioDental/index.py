from flask import render_template, request

from TrioDental import app, dao  # , login, admin


@app.route('/')
def index():
    # q = request.args.get("q")
    # cate_id = request.args.get("cate_id")
    page = request.args.get("page")
    # prods = dao.load_product(q=q, cate_id=cate_id, page=page)
    # pages = math.ceil(dao.count_product() / app.config["PAGE_SIZE"])
    pages = int(page) if page is not None else 1
    return render_template("index.html", pages=pages)#, prods=prods


@app.route("/product-details.html")
def details():
    page = request.args.get("page")
    pages = int(page) if page is not None else 1
    return render_template("product-details.html", pages=pages)

@app.route("/MakeAppointment.html")
def appointment():
    page = request.args.get("page")
    pages = int(page) if page is not None else 1
    return render_template("MakeAppointment.html", pages=pages)

if __name__ == "__main__":
    with app.app_context():
        app.run(debug=True)