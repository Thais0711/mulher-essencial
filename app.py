from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta
from banco import conectar, criar_tabelas

app = Flask(__name__)
criar_tabelas()


def calcular_ciclo(data_ultima_menstruacao, duracao_ciclo):
    data_base = datetime.strptime(data_ultima_menstruacao, "%Y-%m-%d")

    proxima_menstruacao = data_base + timedelta(days=duracao_ciclo)

    ovulacao = proxima_menstruacao - timedelta(days=14)
    fertil_inicio = ovulacao - timedelta(days=3)
    fertil_fim = ovulacao + timedelta(days=2)

    return {
        "proxima_menstruacao": proxima_menstruacao.strftime("%d/%m/%Y"),
        "periodo_fertil_inicio": fertil_inicio.strftime("%d/%m/%Y"),
        "periodo_fertil_fim": fertil_fim.strftime("%d/%m/%Y")
    }


@app.route("/")
def home():
    return redirect(url_for("painel", secao="dashboard"))


@app.route("/painel")
def painel():
    secao = request.args.get("secao", "dashboard")

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM compras ORDER BY id DESC")
    lista_compras = cursor.fetchall()

    cursor.execute("SELECT * FROM agenda ORDER BY data ASC, horario ASC")
    lista_agenda = cursor.fetchall()

    cursor.execute("SELECT * FROM ciclos ORDER BY id DESC")
    lista_ciclos = cursor.fetchall()

    conn.close()

    total_compras = len(lista_compras)
    compras_concluidas = len([item for item in lista_compras if item["status"] == "Concluído"])
    total_agenda = len(lista_agenda)
    total_ciclos = len(lista_ciclos)

    ultimo_ciclo = lista_ciclos[0] if lista_ciclos else None

    return render_template(
        "index.html",
        secao=secao,
        lista_compras=lista_compras,
        lista_agenda=lista_agenda,
        lista_ciclos=lista_ciclos,
        ultimo_ciclo=ultimo_ciclo,
        total_compras=total_compras,
        compras_concluidas=compras_concluidas,
        total_agenda=total_agenda,
        total_ciclos=total_ciclos
    )


@app.route("/adicionar_compra", methods=["POST"])
def adicionar_compra():
    item = request.form["item"]
    quantidade = request.form["quantidade"]
    categoria = request.form["categoria"]
    observacoes = request.form["observacoes"]

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO compras (item, quantidade, categoria, observacoes, status)
        VALUES (?, ?, ?, ?, ?)
    """, (item, quantidade, categoria, observacoes, "Pendente"))

    conn.commit()
    conn.close()

    return redirect(url_for("painel", secao="compras"))


@app.route("/concluir_compra/<int:id>")
def concluir_compra(id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("UPDATE compras SET status = 'Concluído' WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    return redirect(url_for("painel", secao="compras"))


@app.route("/excluir_compra/<int:id>")
def excluir_compra(id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM compras WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    return redirect(url_for("painel", secao="compras"))


@app.route("/editar_compra/<int:id>", methods=["GET", "POST"])
def editar_compra(id):
    conn = conectar()
    cursor = conn.cursor()

    if request.method == "POST":
        item = request.form["item"]
        quantidade = request.form["quantidade"]
        categoria = request.form["categoria"]
        observacoes = request.form["observacoes"]

        cursor.execute("""
            UPDATE compras
            SET item = ?, quantidade = ?, categoria = ?, observacoes = ?
            WHERE id = ?
        """, (item, quantidade, categoria, observacoes, id))

        conn.commit()
        conn.close()
        return redirect(url_for("painel", secao="compras"))

    cursor.execute("SELECT * FROM compras WHERE id = ?", (id,))
    registro = cursor.fetchone()
    conn.close()

    return render_template("editar.html", tipo="compra", registro=registro)


@app.route("/adicionar_agenda", methods=["POST"])
def adicionar_agenda():
    titulo = request.form["titulo"]
    data = request.form["data"]
    horario = request.form["horario"]
    observacoes = request.form["observacoes"]

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO agenda (titulo, data, horario, observacoes)
        VALUES (?, ?, ?, ?)
    """, (titulo, data, horario, observacoes))

    conn.commit()
    conn.close()

    return redirect(url_for("painel", secao="agenda"))


@app.route("/excluir_agenda/<int:id>")
def excluir_agenda(id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM agenda WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    return redirect(url_for("painel", secao="agenda"))


@app.route("/editar_agenda/<int:id>", methods=["GET", "POST"])
def editar_agenda(id):
    conn = conectar()
    cursor = conn.cursor()

    if request.method == "POST":
        titulo = request.form["titulo"]
        data = request.form["data"]
        horario = request.form["horario"]
        observacoes = request.form["observacoes"]

        cursor.execute("""
            UPDATE agenda
            SET titulo = ?, data = ?, horario = ?, observacoes = ?
            WHERE id = ?
        """, (titulo, data, horario, observacoes, id))

        conn.commit()
        conn.close()
        return redirect(url_for("painel", secao="agenda"))

    cursor.execute("SELECT * FROM agenda WHERE id = ?", (id,))
    registro = cursor.fetchone()
    conn.close()

    return render_template("editar.html", tipo="agenda", registro=registro)


@app.route("/adicionar_ciclo", methods=["POST"])
def adicionar_ciclo():
    ultima_menstruacao = request.form["ultima_menstruacao"]
    duracao_ciclo = int(request.form["duracao_ciclo"])
    duracao_fluxo = int(request.form["duracao_fluxo"])
    observacoes = request.form["observacoes"]

    datas = calcular_ciclo(ultima_menstruacao, duracao_ciclo)

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO ciclos (
            ultima_menstruacao,
            duracao_ciclo,
            duracao_fluxo,
            observacoes,
            proxima_menstruacao,
            periodo_fertil_inicio,
            periodo_fertil_fim
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        ultima_menstruacao,
        duracao_ciclo,
        duracao_fluxo,
        observacoes,
        datas["proxima_menstruacao"],
        datas["periodo_fertil_inicio"],
        datas["periodo_fertil_fim"]
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("painel", secao="ciclo"))


@app.route("/excluir_ciclo/<int:id>")
def excluir_ciclo(id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM ciclos WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    return redirect(url_for("painel", secao="ciclo"))


@app.route("/editar_ciclo/<int:id>", methods=["GET", "POST"])
def editar_ciclo(id):
    conn = conectar()
    cursor = conn.cursor()

    if request.method == "POST":
        ultima_menstruacao = request.form["ultima_menstruacao"]
        duracao_ciclo = int(request.form["duracao_ciclo"])
        duracao_fluxo = int(request.form["duracao_fluxo"])
        observacoes = request.form["observacoes"]

        datas = calcular_ciclo(ultima_menstruacao, duracao_ciclo)

        cursor.execute("""
            UPDATE ciclos
            SET ultima_menstruacao = ?, duracao_ciclo = ?, duracao_fluxo = ?,
                observacoes = ?, proxima_menstruacao = ?, periodo_fertil_inicio = ?,
                periodo_fertil_fim = ?
            WHERE id = ?
        """, (
            ultima_menstruacao,
            duracao_ciclo,
            duracao_fluxo,
            observacoes,
            datas["proxima_menstruacao"],
            datas["periodo_fertil_inicio"],
            datas["periodo_fertil_fim"],
            id
        ))

        conn.commit()
        conn.close()
        return redirect(url_for("painel", secao="ciclo"))

    cursor.execute("SELECT * FROM ciclos WHERE id = ?", (id,))
    registro = cursor.fetchone()
    conn.close()

    return render_template("editar.html", tipo="ciclo", registro=registro)


if __name__ == "__main__":
    app.run(debug=True)