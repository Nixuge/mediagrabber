from flask import render_template, redirect

from utils.variables import Global, Constants

app = Global.app


@app.route('/<path:path>', defaults={'path': ''})
def catch_all(path):
    return redirect("/", code=302)


@app.route("/")
@app.route("/index")
@app.route("/index.html")
def index():
    return render_template("index.html", current_api_version=Constants.CAV)


@app.route("/doc")
@app.route("/doc.html")
@app.route("/documentation")
@app.route("/documentation.html")
def doc():
    return render_template("doc.html")


@app.route("/supported")
@app.route("/supported.html")
def supported():
    return render_template("supported.html")
