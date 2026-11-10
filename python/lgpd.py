"""Nordestinando - LGPD (Lei 13.709/2018): aceite versionado, exportação dos dados do titular,
limpeza automática por prazo de retenção e informações do controlador."""
import json
import os
import sqlite3
import time
from datetime import datetime

from flask import Response, jsonify

import banco

VERSAO_TERMOS = "2026-11-10"
VERSAO_PRIVACIDADE = "2026-11-10"
# prazos de retenção (dias) de dados técnicos; dados da conta ficam enquanto ela existir
RETENCAO = {"atividade": 365, "sessao_inativa": 60, "notificacao_lida": 180}


def registrar_aceite(id_usuario):
    banco.conexao().executemany(
        "INSERT INTO consentimento (id_usuario, documento, versao) VALUES (?, ?, ?)",
        [(id_usuario, "termos", VERSAO_TERMOS), (id_usuario, "privacidade", VERSAO_PRIVACIDADE)],
    )


def exigir_aceite(d, erros):
    if d.get("aceite") is not True:
        erros["aceite"] = "Para criar a conta, leia e aceite os Termos de Uso e a Política de Privacidade."


_ultima_limpeza = 0


def limpar_se_preciso():
    global _ultima_limpeza
    if time.time() - _ultima_limpeza > 86400:
        _ultima_limpeza = time.time()
        limpar_antigos()


def limpar_antigos():
    """Elimina dados técnicos vencidos (minimização e limitação da retenção). Roda na inicialização e uma vez por dia."""
    db = sqlite3.connect(banco.CAMINHO_BANCO)
    agora = time.time()
    db.execute("DELETE FROM tentativa WHERE criada_em < ?", (agora - 86400,))
    db.execute("DELETE FROM redefinicao_senha WHERE expira_em < ? OR usada = 1", (agora - 86400,))
    db.execute("DELETE FROM atividade WHERE criada_em < datetime('now', ?)", ("-%d days" % RETENCAO["atividade"],))
    db.execute("DELETE FROM sessao WHERE ultimo_uso < datetime('now', ?)", ("-%d days" % RETENCAO["sessao_inativa"],))
    db.execute("DELETE FROM notificacao WHERE lida = 1 AND criada_em < datetime('now', ?)", ("-%d days" % RETENCAO["notificacao_lida"],))
    db.commit()
    db.close()


def _linhas(db, sql, *args, sem=()):
    return [{k: r[k] for k in r.keys() if k not in sem} for r in db.execute(sql, args).fetchall()]


def exportar(db, u):
    i = u["id_usuario"]
    dados = {
        "gerado_em": datetime.utcnow().isoformat() + "Z",
        "aviso": "Cópia dos seus dados pessoais no Nordestinando (LGPD, art. 18). Senhas e códigos de sessão nunca são incluídos.",
        "conta": {"nome": u["nome"], "email": u["email"], "telefone": u["telefone"], "perfil": u["perfil"], "criado_em": u["criado_em"],
                  "tem_foto": bool(u["avatar"]), "preferencias": json.loads(u["preferencias"] or "{}")},
        "consentimentos": _linhas(db, "SELECT documento, versao, aceito_em FROM consentimento WHERE id_usuario = ?", i),
        "avaliacoes": _linhas(db, "SELECT a.nota, a.comentario, a.crit_atendimento, a.crit_qualidade, a.crit_preco, a.crit_ambiente, a.dica, a.consumiu, a.data_criacao, l.nome_fantasia AS loja, (a.foto IS NOT NULL) AS tem_foto FROM avaliacao a JOIN loja l ON l.id_loja = a.id_loja WHERE a.id_cliente = ?", i),
        "pedidos": _linhas(db, "SELECT p.item, p.valor, p.criado_em, l.nome_fantasia AS loja FROM pedido p JOIN loja l ON l.id_loja = p.id_loja WHERE p.id_cliente = ?", i),
        "carteira": _linhas(db, "SELECT saldo, total_ganho, total_usado FROM carteira WHERE id_usuario = ?", i),
        "movimentos_de_pontos": _linhas(db, "SELECT tipo, pontos, descricao, saldo_apos, criado_em FROM movimento_pontos WHERE id_usuario = ?", i),
        "vouchers": _linhas(db, "SELECT v.codigo, v.status, v.pontos_gastos, v.validade, v.resgatado_em, v.utilizado_em, p.titulo FROM voucher v JOIN promocao p ON p.id_promocao = v.id_promocao WHERE v.id_usuario = ?", i),
        "assinaturas": _linhas(db, "SELECT status, inicio, fim, valor_centavos, ambiente FROM assinatura WHERE id_usuario = ?", i),
        "notificacoes": _linhas(db, "SELECT categoria, titulo, mensagem, lida, criada_em FROM notificacao WHERE id_usuario = ?", i),
        "atividades": _linhas(db, "SELECT acao, detalhe, criada_em FROM atividade WHERE id_usuario = ?", i),
        "sessoes": _linhas(db, "SELECT criado_em, ultimo_uso, ip, agente FROM sessao WHERE id_usuario = ?", i),
    }
    if u["perfil"] == "LOGISTA":
        dados["loja"] = _linhas(db, "SELECT * FROM loja WHERE id_logista = ?", i, sem=("logo", "foto"))
        dados["dados_empresariais"] = _linhas(db, "SELECT cnpj, razao_social FROM logista WHERE id_usuario = ?", i)
        dados["promocoes"] = _linhas(db, "SELECT p.titulo, p.descricao, p.pontos_necessarios, p.inicio, p.fim, p.status FROM promocao p JOIN loja l ON l.id_loja = p.id_loja WHERE l.id_logista = ?", i)
    return dados


def registrar_rotas(app, h):
    exigir, ErroApi = h.exigir, h.ErroApi

    @app.get("/api/lgpd/info")
    def info():
        return jsonify({
            "controlador": os.environ.get("LGPD_CONTROLADOR") or "Equipe Os Bode (projeto Nordestinando)",
            "contato": os.environ.get("LGPD_CONTATO_EMAIL") or None,
            "versao_termos": VERSAO_TERMOS,
            "versao_privacidade": VERSAO_PRIVACIDADE,
            "retencao_dias": RETENCAO,
        })

    @app.get("/api/lgpd/meus-dados")
    @exigir()
    def meus_dados(u):
        db = banco.conexao()
        db.execute("INSERT INTO solicitacao_titular (id_usuario, tipo) VALUES (?, 'acesso')", (u["id_usuario"],))
        dados = exportar(db, u)
        db.commit()
        corpo = json.dumps(dados, ensure_ascii=False, indent=2, default=str)
        return Response(corpo, mimetype="application/json", headers={"Content-Disposition": "attachment; filename=meus-dados-nordestinando.json"})

    @app.get("/api/lgpd/aceite")
    @exigir()
    def meu_aceite(u):
        ult = {r["documento"]: r["versao"] for r in banco.conexao().execute("SELECT documento, versao FROM consentimento WHERE id_usuario = ? ORDER BY id_consentimento", (u["id_usuario"],))}
        return jsonify({"aceitou": ult, "atual": {"termos": VERSAO_TERMOS, "privacidade": VERSAO_PRIVACIDADE},
                        "precisa_reaceitar": ult.get("termos") != VERSAO_TERMOS or ult.get("privacidade") != VERSAO_PRIVACIDADE})

    @app.post("/api/lgpd/aceite")
    @exigir()
    def aceitar(u):
        d = h.dados_json()
        if d.get("aceite") is not True:
            raise ErroApi("É preciso aceitar para continuar usando a conta.", {"aceite": "Marque a caixa para aceitar."})
        registrar_aceite(u["id_usuario"])
        banco.conexao().commit()
        return jsonify({"ok": True})
