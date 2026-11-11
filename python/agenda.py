"""Nordestinando - agenda de eventos da cidade (feiras, encontros etc.).

Os eventos ficam na tabela evento_cidade. Eles juntam-se aos eventos que os comerciantes
anunciam, e a tela monta os cards, filtros e detalhes sozinha: não precisa mexer no layout.
"""
import json
import os
import sqlite3

from flask import jsonify, request

import banco

ARQUIVO_SEED = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados", "eventos_cidade.json")
DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
PERIODOS = {"manha": "Manhã", "tarde": "Tarde", "noite": "Noite"}


def semear():
    """Insere os eventos do arquivo JSON e atualiza os que já existem (o arquivo é a fonte; edite-o para corrigir um evento)."""
    if not os.path.exists(ARQUIVO_SEED):
        return
    with open(ARQUIVO_SEED, encoding="utf-8") as f:
        eventos = json.load(f)
    con = sqlite3.connect(banco.CAMINHO_BANCO)
    for e in eventos:
        con.execute(
            """INSERT INTO evento_cidade
               (slug, titulo, categoria, dia_semana, periodo, horario, local_nome, busca_mapa, latitude, longitude,
                descricao, detalhes, pendencias, foto)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(slug) DO UPDATE SET titulo = excluded.titulo, categoria = excluded.categoria, dia_semana = excluded.dia_semana,
                 periodo = excluded.periodo, horario = excluded.horario, local_nome = excluded.local_nome, busca_mapa = excluded.busca_mapa,
                 descricao = excluded.descricao, detalhes = excluded.detalhes, pendencias = excluded.pendencias, foto = excluded.foto""",
            (
                e["slug"], e["titulo"], e["categoria"], e["dia_semana"], e["periodo"], e.get("horario"),
                e["local_nome"], e.get("busca_mapa"), e.get("latitude"), e.get("longitude"), e["descricao"],
                json.dumps(e.get("detalhes", []), ensure_ascii=False),
                json.dumps(e.get("pendencias", []), ensure_ascii=False), e.get("foto"),
            ),
        )
    con.commit()
    con.close()


def periodo_do_horario(horario):
    try:
        hora = int(str(horario).split(":")[0])
    except (ValueError, IndexError):
        return "noite"
    return "manha" if hora < 12 else "tarde" if hora < 18 else "noite"


def registrar_rotas(app):
    @app.get("/api/agenda")
    def agenda():
        db = banco.conexao()
        itens = []
        for e in db.execute("SELECT * FROM evento_cidade WHERE ativo = 1"):
            itens.append(
                {
                    "id": "cidade-%d" % e["id_evento_cidade"],
                    "origem": "cidade",
                    "titulo": e["titulo"],
                    "categoria": e["categoria"],
                    "dia": e["dia_semana"],
                    "periodo": e["periodo"],
                    "periodo_rotulo": PERIODOS[e["periodo"]],
                    "horario": e["horario"],
                    "local": e["local_nome"],
                    "busca_mapa": e["busca_mapa"],
                    "latitude": e["latitude"],
                    "longitude": e["longitude"],
                    "descricao": e["descricao"],
                    "detalhes": json.loads(e["detalhes"]),
                    "pendencias": json.loads(e["pendencias"]),
                    "foto": e["foto"],
                    "id_loja": None,
                }
            )
        # eventos anunciados pelos comerciantes
        for e in db.execute(
            """SELECT e.*, l.nome_fantasia, l.rua, l.numero, l.bairro, l.cidade, l.latitude AS lat_loja, l.longitude AS lng_loja
               FROM evento e JOIN loja l ON l.id_loja = e.id_loja"""
        ):
            periodo = periodo_do_horario(e["horario"])
            itens.append(
                {
                    "id": "loja-%d" % e["id_evento"],
                    "origem": "loja",
                    "titulo": e["nome"],
                    "categoria": "Eventos de lojas",
                    "dia": e["dia_semana"],
                    "periodo": periodo,
                    "periodo_rotulo": PERIODOS[periodo],
                    "horario": e["horario"],
                    "local": e["nome_fantasia"],
                    "busca_mapa": None,
                    "latitude": e["latitude"] if e["latitude"] is not None else e["lat_loja"],
                    "longitude": e["longitude"] if e["longitude"] is not None else e["lng_loja"],
                    "descricao": e["descricao"] or "",
                    "detalhes": ["Endereço: %s, %s - %s, %s" % (e["rua"], e["numero"], e["bairro"], e["cidade"])],
                    "pendencias": [],
                    "foto": None,
                    "id_loja": e["id_loja"],
                }
            )
        ordem = {d: i for i, d in enumerate(DIAS)}
        ordem_periodo = {"manha": 0, "tarde": 1, "noite": 2}
        itens.sort(key=lambda i: (ordem.get(i["dia"], 9), ordem_periodo[i["periodo"]], i["titulo"]))
        categorias = sorted({i["categoria"] for i in itens})
        return jsonify({"eventos": itens, "categorias": categorias, "dias": DIAS})
