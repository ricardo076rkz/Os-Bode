"""Conexão com o banco (SQLite, biblioteca padrão do Python)."""
import os
import sqlite3

from flask import g

PASTA = os.path.dirname(os.path.abspath(__file__))
CAMINHO_BANCO = os.environ.get("DB_PATH") or os.path.join(PASTA, "nordestinando.db")


def conexao():
    # uma conexão por requisição
    if "db" not in g:
        g.db = sqlite3.connect(CAMINHO_BANCO)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def fechar(erro=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def criar_tabelas():
    with open(os.path.join(PASTA, "schema.sql"), encoding="utf-8") as f:
        script = f.read()
    con = sqlite3.connect(CAMINHO_BANCO)
    con.executescript(script)
    # bancos criados antes desta versão ganham as colunas novas
    colunas = {c[1] for c in con.execute("PRAGMA table_info(usuario)")}
    if "avatar" not in colunas:
        con.execute("ALTER TABLE usuario ADD COLUMN avatar TEXT")
    if "preferencias" not in colunas:
        con.execute("ALTER TABLE usuario ADD COLUMN preferencias TEXT NOT NULL DEFAULT '{}'")
    # avaliações com critérios, dica, foto e controle de pontos
    colunas = {c[1] for c in con.execute("PRAGMA table_info(avaliacao)")}
    for nome, tipo in (
        ("crit_atendimento", "INTEGER"), ("crit_qualidade", "INTEGER"), ("crit_preco", "INTEGER"), ("crit_ambiente", "INTEGER"),
        ("dica", "TEXT"), ("consumiu", "TEXT"), ("foto", "TEXT"), ("pontos_base_concedidos", "INTEGER NOT NULL DEFAULT 0"),
    ):
        if nome not in colunas:
            con.execute("ALTER TABLE avaliacao ADD COLUMN %s %s" % (nome, tipo))
    con.commit()
    con.close()
