from flask import Flask, render_template, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = "mulher_essencial_chave"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/cadastro")
def cadastro():
    flash("Página de cadastro em construção 💖", "warning")
    return redirect(url_for("index"))

@app.route("/login")
def login():
    flash("Página de login em construção 🔐", "warning")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)