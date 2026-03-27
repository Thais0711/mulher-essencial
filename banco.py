import sqlite3

def conectar():
    conn = sqlite3.connect("mulher_essencial.db")
    conn.row_factory = sqlite3.Row
    return conn

def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT NOT NULL,
            quantidade TEXT NOT NULL,
            categoria TEXT NOT NULL,
            observacoes TEXT,
            status TEXT DEFAULT 'Pendente'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agenda (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            data TEXT NOT NULL,
            horario TEXT NOT NULL,
            observacoes TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ciclos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ultima_menstruacao TEXT NOT NULL,
            duracao_ciclo INTEGER NOT NULL,
            duracao_fluxo INTEGER NOT NULL,
            observacoes TEXT,
            proxima_menstruacao TEXT,
            periodo_fertil_inicio TEXT,
            periodo_fertil_fim TEXT
        )
    """)

    try:
        cursor.execute("ALTER TABLE compras ADD COLUMN status TEXT DEFAULT 'Pendente'")
    except:
        pass

    conn.commit()
    conn.close()