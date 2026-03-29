from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "mulher_essencial_chave_secreta_2026"

DB_NAME = "mulher_essencial.db"


def conectar():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            item TEXT NOT NULL,
            quantidade TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agenda (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            data TEXT NOT NULL,
            hora TEXT,
            descricao TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ciclo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            data_inicio TEXT NOT NULL,
            duracao_ciclo INTEGER NOT NULL DEFAULT 28,
            observacoes TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)

    conn.commit()
    conn.close()


def atualizar_tabela_ciclo():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(ciclo)")
    colunas = [col["name"] for col in cursor.fetchall()]

    if "duracao_ciclo" not in colunas:
        cursor.execute("ALTER TABLE ciclo ADD COLUMN duracao_ciclo INTEGER NOT NULL DEFAULT 28")
        conn.commit()

    conn.close()


def login_obrigatorio(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Faça login para continuar.", "erro")
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper


def calcular_previsao_ciclo(data_inicio_str, duracao_ciclo):
    data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d").date()

    proxima_menstruacao = data_inicio + timedelta(days=duracao_ciclo)
    ovulacao = proxima_menstruacao - timedelta(days=14)
    fertil_inicio = ovulacao - timedelta(days=5)
    fertil_fim = ovulacao + timedelta(days=1)

    return {
        "proxima_menstruacao": proxima_menstruacao.strftime("%d/%m/%Y"),
        "ovulacao": ovulacao.strftime("%d/%m/%Y"),
        "fertil_inicio": fertil_inicio.strftime("%d/%m/%Y"),
        "fertil_fim": fertil_fim.strftime("%d/%m/%Y")
    }


criar_tabelas()
atualizar_tabela_ciclo()


@app.route("/")
def index():
    if "usuario_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "").strip()

        if not nome or not email or not senha:
            flash("Preencha todos os campos.", "erro")
            return render_template("cadastro.html")

        senha_hash = generate_password_hash(senha)

        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
                (nome, email, senha_hash)
            )
            conn.commit()
            conn.close()

            flash("Cadastro realizado com sucesso. Faça login.", "sucesso")
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            flash("Este e-mail já está cadastrado.", "erro")

    return render_template("cadastro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "").strip()

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
        usuario = cursor.fetchone()
        conn.close()

        if usuario and check_password_hash(usuario["senha"], senha):
            session["usuario_id"] = usuario["id"]
            session["usuario_nome"] = usuario["nome"]
            flash("Login realizado com sucesso.", "sucesso")
            return redirect(url_for("dashboard"))
        else:
            flash("E-mail ou senha inválidos.", "erro")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu da sua conta.", "sucesso")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_obrigatorio
def dashboard():
    usuario_id = session["usuario_id"]

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS total FROM compras WHERE usuario_id = ?", (usuario_id,))
    total_compras = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM agenda WHERE usuario_id = ?", (usuario_id,))
    total_agenda = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM ciclo WHERE usuario_id = ?", (usuario_id,))
    total_ciclo = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT * FROM ciclo
        WHERE usuario_id = ?
        ORDER BY data_inicio DESC, id DESC
        LIMIT 1
    """, (usuario_id,))
    ultimo_ciclo = cursor.fetchone()

    previsao = None
    if ultimo_ciclo:
        previsao = calcular_previsao_ciclo(
            ultimo_ciclo["data_inicio"],
            ultimo_ciclo["duracao_ciclo"]
        )

    conn.close()

    return render_template(
        "dashboard.html",
        total_compras=total_compras,
        total_agenda=total_agenda,
        total_ciclo=total_ciclo,
        previsao=previsao
    )


@app.route("/compras", methods=["GET", "POST"])
@login_obrigatorio
def compras():
    usuario_id = session["usuario_id"]
    conn = conectar()
    cursor = conn.cursor()

    if request.method == "POST":
        item = request.form.get("item", "").strip()
        quantidade = request.form.get("quantidade", "").strip()

        if item:
            cursor.execute(
                "INSERT INTO compras (usuario_id, item, quantidade) VALUES (?, ?, ?)",
                (usuario_id, item, quantidade)
            )
            conn.commit()
            flash("Item adicionado com sucesso.", "sucesso")
        else:
            flash("Informe o nome do item.", "erro")

    cursor.execute(
        "SELECT * FROM compras WHERE usuario_id = ? ORDER BY id DESC",
        (usuario_id,)
    )
    lista_compras = cursor.fetchall()
    conn.close()

    return render_template("compras.html", lista_compras=lista_compras)


@app.route("/excluir_compra/<int:item_id>")
@login_obrigatorio
def excluir_compra(item_id):
    usuario_id = session["usuario_id"]

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM compras WHERE id = ? AND usuario_id = ?",
        (item_id, usuario_id)
    )
    conn.commit()
    conn.close()

    flash("Item removido com sucesso.", "sucesso")
    return redirect(url_for("compras"))


@app.route("/agenda", methods=["GET", "POST"])
@login_obrigatorio
def agenda():
    usuario_id = session["usuario_id"]
    conn = conectar()
    cursor = conn.cursor()

    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        data = request.form.get("data", "").strip()
        hora = request.form.get("hora", "").strip()
        descricao = request.form.get("descricao", "").strip()

        if titulo and data:
            cursor.execute("""
                INSERT INTO agenda (usuario_id, titulo, data, hora, descricao)
                VALUES (?, ?, ?, ?, ?)
            """, (usuario_id, titulo, data, hora, descricao))
            conn.commit()
            flash("Compromisso salvo com sucesso.", "sucesso")
        else:
            flash("Preencha pelo menos título e data.", "erro")

    cursor.execute("""
        SELECT * FROM agenda
        WHERE usuario_id = ?
        ORDER BY data ASC, hora ASC, id DESC
    """, (usuario_id,))
    compromissos = cursor.fetchall()
    conn.close()

    return render_template("agenda.html", compromissos=compromissos)


@app.route("/excluir_agenda/<int:agenda_id>")
@login_obrigatorio
def excluir_agenda(agenda_id):
    usuario_id = session["usuario_id"]

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM agenda WHERE id = ? AND usuario_id = ?",
        (agenda_id, usuario_id)
    )
    conn.commit()
    conn.close()

    flash("Compromisso excluído com sucesso.", "sucesso")
    return redirect(url_for("agenda"))


@app.route("/ciclo", methods=["GET", "POST"])
@login_obrigatorio
def ciclo():
    usuario_id = session["usuario_id"]
    conn = conectar()
    cursor = conn.cursor()

    if request.method == "POST":
        data_inicio = request.form.get("data_inicio", "").strip()
        duracao_ciclo = request.form.get("duracao_ciclo", "").strip()
        observacoes = request.form.get("observacoes", "").strip()

        if not data_inicio:
            flash("Informe a data de início.", "erro")
        else:
            try:
                duracao_ciclo = int(duracao_ciclo) if duracao_ciclo else 28

                cursor.execute("""
                    INSERT INTO ciclo (usuario_id, data_inicio, duracao_ciclo, observacoes)
                    VALUES (?, ?, ?, ?)
                """, (usuario_id, data_inicio, duracao_ciclo, observacoes))
                conn.commit()
                flash("Registro do ciclo salvo com sucesso.", "sucesso")
            except ValueError:
                flash("A duração do ciclo precisa ser um número.", "erro")

    cursor.execute("""
        SELECT * FROM ciclo
        WHERE usuario_id = ?
        ORDER BY data_inicio DESC, id DESC
    """, (usuario_id,))
    registros = cursor.fetchall()
    conn.close()

    registros_com_previsao = []
    for r in registros:
        previsao = calcular_previsao_ciclo(r["data_inicio"], r["duracao_ciclo"])
        registros_com_previsao.append({
            "id": r["id"],
            "data_inicio": r["data_inicio"],
            "duracao_ciclo": r["duracao_ciclo"],
            "observacoes": r["observacoes"],
            "proxima_menstruacao": previsao["proxima_menstruacao"],
            "ovulacao": previsao["ovulacao"],
            "fertil_inicio": previsao["fertil_inicio"],
            "fertil_fim": previsao["fertil_fim"]
        })

    return render_template("ciclo.html", registros=registros_com_previsao)


@app.route("/excluir_ciclo/<int:ciclo_id>")
@login_obrigatorio
def excluir_ciclo(ciclo_id):
    usuario_id = session["usuario_id"]

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM ciclo WHERE id = ? AND usuario_id = ?",
        (ciclo_id, usuario_id)
    )
    conn.commit()
    conn.close()

    flash("Registro excluído com sucesso.", "sucesso")
    return redirect(url_for("ciclo"))


if __name__ == "__main__":
    app.run(debug=True)