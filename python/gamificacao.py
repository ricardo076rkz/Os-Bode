"""Nordestinando - gamificação: pontos por avaliação, carteira, promoções, vouchers e Nordestinando+.

Regras importantes (todas calculadas AQUI, no servidor; o navegador só mostra):
- a nota (positiva ou negativa) nunca entra na conta dos pontos;
- cada movimentação de pontos fica no razão `movimento_pontos`, com uma chave única (sem recompensa em duplicidade);
- o resgate de um voucher debita os pontos, baixa o estoque e cria o voucher numa única transação;
- um voucher só pode ser usado uma vez.
As regras de pontuação ficam em python/dados/regras_pontos.json.
"""
import hmac
import hashlib
import json
import os
import re
import secrets
import sqlite3
from datetime import date, datetime, timedelta

from flask import jsonify, request

import banco
import conta

ARQUIVO_REGRAS = os.environ.get("REGRAS_PONTOS") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados", "regras_pontos.json")
with open(ARQUIVO_REGRAS, encoding="utf-8") as _f:
    REGRAS = json.load(_f)

TIPOS_BENEFICIO = {
    "percentual": "Desconto percentual",
    "valor_fixo": "Desconto em valor fixo",
    "brinde": "Brinde",
    "especial": "Promoção especial",
    "outro": "Outro benefício",
}
ALFABETO_CODIGO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sem 0/O/1/I para não confundir na hora de digitar


def hoje():
    return date.today().isoformat()


# ---------------------------------------------------------------- cálculo de pontos
def _tamanho_util(texto):
    """Tamanho do texto só se ele parece um texto de verdade (evita 'aaaaaaaa...' ou repetição)."""
    texto = (texto or "").strip()
    palavras = set(re.findall(r"\w+", texto.lower()))
    if len(palavras) < 3 or len(set(texto.replace(" ", ""))) < 6:
        return 0
    return len(texto)


def extras_da_linha(linha):
    """Dados que valem pontos, lidos da avaliação já gravada."""
    return {
        "criterios": {c: linha["crit_" + c] for c in REGRAS["criterios"] if linha["crit_" + c]},
        "comentario": linha["comentario"] or "",
        "dica": linha["dica"] or "",
        "consumiu": linha["consumiu"] or "",
        "foto": bool(linha["foto"]),
    }


def calcular(extras, multiplicador=1):
    """Pontuação progressiva e transparente. Não olha a nota."""
    r = REGRAS
    n_crit = len(extras["criterios"])
    tam_comentario = _tamanho_util(extras["comentario"])
    minimo = r["minimo_para_pontuar"]
    valido = n_crit >= minimo["criterios"] or tam_comentario >= minimo["comentario_min_caracteres"]
    saida = {"valido": valido, "itens": [], "base": 0, "multiplicador": multiplicador, "total": 0, "bonus": 0, "motivo": None}
    if not valido:
        saida["motivo"] = "Para ganhar pontos, preencha pelo menos %d critérios ou escreva um comentário de %d letras ou mais." % (
            minimo["criterios"], minimo["comentario_min_caracteres"])
        return saida
    itens = [("Avaliação válida", r["base_avaliacao_valida"])]
    if n_crit:
        itens.append(("%d critério(s) avaliado(s)" % n_crit, n_crit * r["pontos_por_criterio"]))
    faixa = None
    for f in r["faixas_comentario"]:
        if tam_comentario >= f["min_caracteres"]:
            faixa = f
    if faixa:
        itens.append((faixa["rotulo"], faixa["pontos"]))
    if _tamanho_util(extras["dica"]) >= r["dica"]["min_caracteres"]:
        itens.append(("Dica para outros visitantes", r["dica"]["pontos"]))
    if len((extras["consumiu"] or "").strip()) >= r["consumiu"]["min_caracteres"]:
        itens.append(("Informou o que consumiu", r["consumiu"]["pontos"]))
    if extras["foto"]:
        itens.append(("Foto", r["foto"]["pontos"]))
    saida["itens"] = [{"rotulo": a, "pontos": b} for a, b in itens]
    saida["base"] = sum(b for _, b in itens)
    saida["total"] = saida["base"] * multiplicador
    saida["bonus"] = saida["total"] - saida["base"]
    return saida


def ler_extras(d, h, existente=None):
    """Lê e valida os campos opcionais da avaliação. `existente` mantém o que já estava gravado (ex.: foto)."""
    erros = {}
    criterios = {}
    for c in REGRAS["criterios"]:
        v = d.get("crit_" + c)
        if v in (None, "", 0):
            continue
        try:
            v = int(v)
            assert 1 <= v <= 5
            criterios[c] = v
        except (TypeError, ValueError, AssertionError):
            erros["crit_" + c] = "Use uma nota de 1 a 5."
    if erros:
        raise h.ErroApi("Corrija os campos destacados.", erros)
    foto = None
    if d.get("foto"):
        foto = h.imagem_valida(d.get("foto"))
    return {
        "criterios": criterios,
        "comentario": h.texto(d, "comentario", 600),
        "dica": h.texto(d, "dica", 200),
        "consumiu": h.texto(d, "consumiu", 80),
        "foto_nova": foto,
        "foto": bool(foto) or bool(existente is not None and existente["foto"]),
    }


# ---------------------------------------------------------------- planos (Nordestinando+)
def estado_plano(db, id_usuario):
    a = db.execute("SELECT * FROM assinatura WHERE id_usuario = ? ORDER BY id_assinatura DESC LIMIT 1", (id_usuario,)).fetchone()
    if a is None:
        estado = "gratuito"
    elif a["status"] == "cancelada":
        estado = "premium_cancelado"
    elif a["fim"] < hoje():
        estado = "premium_expirado"
    else:
        estado = "premium_ativo"
    return {
        "estado": estado,
        "multiplicador": REGRAS["multiplicador_premium"] if estado == "premium_ativo" else 1,
        "inicio": a["inicio"] if a else None,
        "fim": a["fim"] if a else None,
        "ambiente": a["ambiente"] if a else None,
    }


# ---------------------------------------------------------------- carteira
def garantir_carteira(db, id_usuario):
    db.execute("INSERT OR IGNORE INTO carteira (id_usuario) VALUES (?)", (id_usuario,))


def carteira_dict(db, id_usuario):
    garantir_carteira(db, id_usuario)
    c = db.execute("SELECT * FROM carteira WHERE id_usuario = ?", (id_usuario,)).fetchone()
    niveis = REGRAS["niveis"]
    ganho = c["total_ganho"]
    atual = niveis[0]
    for n in niveis:
        if ganho >= n["min_pontos"]:
            atual = n
    proximo = next((n for n in niveis if n["min_pontos"] > ganho), None)
    if proximo:
        faixa = proximo["min_pontos"] - atual["min_pontos"]
        progresso = round((ganho - atual["min_pontos"]) * 100 / faixa)
    else:
        progresso = 100
    bonus = db.execute("SELECT COALESCE(SUM(pontos_bonus), 0) FROM movimento_pontos WHERE id_usuario = ? AND tipo = 'avaliacao'", (id_usuario,)).fetchone()[0]
    return {
        "saldo": c["saldo"],
        "total_ganho": ganho,
        "total_usado": c["total_usado"],
        "bonus_premium": bonus,
        "nivel": {
            "nome": atual["nome"],
            "proximo": proximo["nome"] if proximo else None,
            "faltam": (proximo["min_pontos"] - ganho) if proximo else 0,
            "progresso": progresso,
        },
    }


def verificar_saldo(db, id_usuario):
    """Consistência: o saldo deve ser a soma de tudo que está no razão."""
    soma = db.execute("SELECT COALESCE(SUM(pontos), 0) FROM movimento_pontos WHERE id_usuario = ?", (id_usuario,)).fetchone()[0]
    saldo = db.execute("SELECT saldo FROM carteira WHERE id_usuario = ?", (id_usuario,)).fetchone()
    return soma == (saldo["saldo"] if saldo else 0)


def conceder_pontos_avaliacao(db, usuario, id_loja, id_avaliacao, linha, pontos_base_anteriores):
    """Chamado dentro da transação da avaliação. Devolve um resumo do que foi ganho."""
    plano = estado_plano(db, usuario["id_usuario"])
    calc = calcular(extras_da_linha(linha), plano["multiplicador"])
    resposta = {"pontos": 0, "base": 0, "bonus": 0, "multiplicador": plano["multiplicador"], "itens": calc["itens"], "motivo": calc["motivo"], "premium": plano["multiplicador"] > 1}
    if not calc["valido"]:
        return resposta
    novo_base = calc["base"] - pontos_base_anteriores
    if novo_base <= 0:
        resposta["motivo"] = "Você já ganhou os pontos desta avaliação. Complete mais itens para ganhar a diferença."
        return resposta
    limite = REGRAS["limite_diario_avaliacoes_pontuadas"]
    hoje_n = db.execute(
        "SELECT COUNT(*) FROM movimento_pontos WHERE id_usuario = ? AND tipo = 'avaliacao' AND date(criado_em) = date('now')",
        (usuario["id_usuario"],),
    ).fetchone()[0]
    if hoje_n >= limite:
        resposta["motivo"] = "Limite diário de avaliações com pontos atingido (%d). A avaliação foi salva; volte amanhã para ganhar mais." % limite
        return resposta
    mult = plano["multiplicador"]
    total = novo_base * mult
    garantir_carteira(db, usuario["id_usuario"])
    db.execute("UPDATE carteira SET saldo = saldo + ?, total_ganho = total_ganho + ? WHERE id_usuario = ?", (total, total, usuario["id_usuario"]))
    saldo = db.execute("SELECT saldo FROM carteira WHERE id_usuario = ?", (usuario["id_usuario"],)).fetchone()["saldo"]
    loja = db.execute("SELECT nome_fantasia FROM loja WHERE id_loja = ?", (id_loja,)).fetchone()
    try:
        db.execute(
            """INSERT INTO movimento_pontos (id_usuario, tipo, pontos, pontos_base, pontos_bonus, multiplicador, descricao, id_loja, id_avaliacao, chave, saldo_apos)
               VALUES (?, 'avaliacao', ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (usuario["id_usuario"], total, novo_base, total - novo_base, mult, "Avaliação de %s" % loja["nome_fantasia"], id_loja, id_avaliacao,
             "aval:%d:%d" % (id_avaliacao, calc["base"]), saldo),
        )
    except sqlite3.IntegrityError:  # a mesma recompensa já foi registrada
        raise ValueError("duplicada")
    db.execute("UPDATE avaliacao SET pontos_base_concedidos = ? WHERE id_avaliacao = ?", (calc["base"], id_avaliacao))
    resposta.update({"pontos": total, "base": novo_base, "bonus": total - novo_base, "saldo": saldo})
    return resposta


# ---------------------------------------------------------------- vouchers
def estado_voucher(v):
    if v["status"] == "resgatado" and v["validade"] < hoje():
        return "expirado"
    return v["status"]


ROTULO_ESTADO = {"resgatado": "Resgatado", "utilizado": "Utilizado", "expirado": "Expirado", "cancelado": "Cancelado"}


def descricao_beneficio(p):
    tipo = p["tipo_beneficio"]
    v = p["valor_beneficio"]
    if tipo == "percentual" and v:
        return "%g%% de desconto" % v
    if tipo == "valor_fixo" and v:
        return "R$ %.2f de desconto" % v
    return TIPOS_BENEFICIO[tipo]


def novo_codigo(db):
    for _ in range(20):
        c = "".join(secrets.choice(ALFABETO_CODIGO) for _ in range(8))
        c = "NORD-%s-%s" % (c[:4], c[4:])
        if not db.execute("SELECT 1 FROM voucher WHERE codigo = ?", (c,)).fetchone():
            return c
    raise RuntimeError("não foi possível gerar código")


def iniciar_escrita(db):
    if not db.in_transaction:
        db.execute("BEGIN IMMEDIATE")


# ---------------------------------------------------------------- rotas
def registrar_rotas(app, h):
    ErroApi, dados_json, texto, exigir = h.ErroApi, h.dados_json, h.texto, h.exigir

    def promocao_dict(p, loja, usuario=None, db=None):
        restantes = p["quantidade_total"] - p["quantidade_resgatada"]
        saida = {
            "id": p["id_promocao"],
            "titulo": p["titulo"],
            "descricao": p["descricao"],
            "tipo": p["tipo_beneficio"],
            "tipo_rotulo": TIPOS_BENEFICIO[p["tipo_beneficio"]],
            "beneficio": descricao_beneficio(p),
            "valor": p["valor_beneficio"],
            "pontos": p["pontos_necessarios"],
            "restantes": restantes,
            "validade": p["fim"],
            "inicio": p["inicio"],
            "condicoes": p["condicoes"],
            "limite_por_usuario": p["limite_por_usuario"],
            "loja": {"id": loja["id_loja"], "nome": loja["nome_fantasia"], "logo": loja["logo"], "foto": loja["foto"], "bairro": loja["bairro"]},
        }
        return saida

    # ---------- estimativa antes de enviar
    @app.post("/api/pontos/estimativa")
    @exigir("CLIENTE")
    def estimativa(usuario):
        d = dados_json()
        db = banco.conexao()
        existente = None
        if d.get("id_loja"):
            existente = db.execute("SELECT * FROM avaliacao WHERE id_cliente = ? AND id_loja = ?", (usuario["id_usuario"], d["id_loja"])).fetchone()
        extras = ler_extras(d, h, existente)
        plano = estado_plano(db, usuario["id_usuario"])
        calc = calcular(extras, plano["multiplicador"])
        ja = existente["pontos_base_concedidos"] if existente else 0
        a_receber = max(0, calc["base"] - ja) if calc["valido"] else 0
        calc["ja_pontuado"] = ja
        calc["a_receber"] = a_receber * plano["multiplicador"]
        calc["premium"] = plano["multiplicador"] > 1
        calc["maximo_possivel"] = None
        return jsonify({"estimativa": calc})

    @app.get("/api/pontos/regras")
    def regras_publicas():
        r = REGRAS
        return jsonify({"regras": {k: r[k] for k in ("base_avaliacao_valida", "pontos_por_criterio", "criterios", "faixas_comentario", "dica", "consumiu", "foto", "minimo_para_pontuar", "limite_diario_avaliacoes_pontuadas", "multiplicador_premium")}})

    # ---------- carteira
    @app.get("/api/carteira")
    @exigir("CLIENTE")
    def ver_carteira(usuario):
        db = banco.conexao()
        saida = carteira_dict(db, usuario["id_usuario"])
        saida["plano"] = estado_plano(db, usuario["id_usuario"])
        saida["vouchers_ativos"] = db.execute(
            "SELECT COUNT(*) FROM voucher WHERE id_usuario = ? AND status = 'resgatado' AND validade >= ?", (usuario["id_usuario"], hoje())
        ).fetchone()[0]
        db.commit()
        return jsonify({"carteira": saida})

    @app.get("/api/carteira/movimentos")
    @exigir("CLIENTE")
    def movimentos(usuario):
        filtro = request.args.get("tipo", "todos")
        where = {"ganhos": "AND pontos > 0", "usos": "AND pontos < 0", "bonus": "AND pontos_bonus > 0"}.get(filtro, "")
        linhas = banco.conexao().execute(
            "SELECT * FROM movimento_pontos WHERE id_usuario = ? %s ORDER BY id_movimento DESC LIMIT 100" % where, (usuario["id_usuario"],)
        ).fetchall()
        return jsonify({"movimentos": [{k: m[k] for k in ("id_movimento", "tipo", "pontos", "pontos_base", "pontos_bonus", "multiplicador", "descricao", "saldo_apos", "criado_em")} for m in linhas]})

    def voucher_dict(v, p, loja):
        est = estado_voucher(v)
        return {
            "id": v["id_voucher"], "codigo": v["codigo"], "estado": est, "estado_rotulo": ROTULO_ESTADO[est],
            "pontos": v["pontos_gastos"], "validade": v["validade"], "resgatado_em": v["resgatado_em"], "utilizado_em": v["utilizado_em"],
            "titulo": p["titulo"], "beneficio": descricao_beneficio(p), "condicoes": p["condicoes"],
            "loja": {"id": loja["id_loja"], "nome": loja["nome_fantasia"], "bairro": loja["bairro"], "rua": loja["rua"], "numero": loja["numero"]},
        }

    @app.get("/api/carteira/vouchers")
    @exigir("CLIENTE")
    def meus_vouchers(usuario):
        db = banco.conexao()
        linhas = db.execute(
            """SELECT v.*, p.titulo, p.tipo_beneficio, p.valor_beneficio, p.condicoes, l.id_loja, l.nome_fantasia, l.bairro, l.rua, l.numero
               FROM voucher v JOIN promocao p ON p.id_promocao = v.id_promocao JOIN loja l ON l.id_loja = p.id_loja
               WHERE v.id_usuario = ? ORDER BY v.id_voucher DESC""",
            (usuario["id_usuario"],),
        ).fetchall()
        return jsonify({"vouchers": [voucher_dict(v, v, v) for v in linhas]})

    # ---------- recompensas (promoções dos parceiros)
    @app.get("/api/recompensas")
    def listar_recompensas():
        db = banco.conexao()
        usuario = h.usuario_logado()
        cliente = usuario is not None and usuario["perfil"] == "CLIENTE"
        saldo = carteira_dict(db, usuario["id_usuario"])["saldo"] if cliente else None
        linhas = db.execute(
            """SELECT p.*, l.id_loja, l.nome_fantasia, l.logo, l.foto, l.bairro FROM promocao p JOIN loja l ON l.id_loja = p.id_loja
               WHERE p.status = 'ativa' AND p.inicio <= ? AND p.fim >= ? AND p.quantidade_resgatada < p.quantidade_total
               ORDER BY p.pontos_necessarios ASC, p.id_promocao DESC""",
            (hoje(), hoje()),
        ).fetchall()
        saida = []
        for p in linhas:
            item = promocao_dict(p, p)
            if cliente:
                usados = db.execute("SELECT COUNT(*) FROM voucher WHERE id_usuario = ? AND id_promocao = ? AND status != 'cancelado'", (usuario["id_usuario"], p["id_promocao"])).fetchone()[0]
                item["ja_resgatou"] = usados
                item["pode_resgatar"] = saldo >= p["pontos_necessarios"] and usados < p["limite_por_usuario"]
                item["faltam"] = max(0, p["pontos_necessarios"] - saldo)
            saida.append(item)
        db.commit()
        return jsonify({"recompensas": saida, "saldo": saldo})

    @app.post("/api/recompensas/<int:id_promocao>/resgatar")
    @exigir("CLIENTE")
    def resgatar(usuario, id_promocao):
        db = banco.conexao()
        try:
            iniciar_escrita(db)  # a partir daqui: tudo ou nada
            p = db.execute(
                "SELECT p.*, l.id_loja, l.nome_fantasia, l.id_logista, l.bairro, l.rua, l.numero FROM promocao p JOIN loja l ON l.id_loja = p.id_loja WHERE p.id_promocao = ?",
                (id_promocao,),
            ).fetchone()
            if p is None:
                raise ErroApi("Recompensa não encontrada.", status=404)
            if p["status"] != "ativa" or not (p["inicio"] <= hoje() <= p["fim"]):
                raise ErroApi("Esta recompensa não está disponível agora.", status=400)
            if p["quantidade_resgatada"] >= p["quantidade_total"]:
                raise ErroApi("Esta recompensa esgotou.", status=400)
            usados = db.execute("SELECT COUNT(*) FROM voucher WHERE id_usuario = ? AND id_promocao = ? AND status != 'cancelado'", (usuario["id_usuario"], id_promocao)).fetchone()[0]
            if usados >= p["limite_por_usuario"]:
                raise ErroApi("Você já resgatou o máximo permitido desta recompensa.", status=400)
            garantir_carteira(db, usuario["id_usuario"])
            custo = p["pontos_necessarios"]
            cur = db.execute("UPDATE carteira SET saldo = saldo - ?, total_usado = total_usado + ? WHERE id_usuario = ? AND saldo >= ?", (custo, custo, usuario["id_usuario"], custo))
            if cur.rowcount == 0:
                saldo = db.execute("SELECT saldo FROM carteira WHERE id_usuario = ?", (usuario["id_usuario"],)).fetchone()["saldo"]
                raise ErroApi("Pontos insuficientes. Faltam %d pontos." % (custo - saldo), status=400)
            cur = db.execute(
                "UPDATE promocao SET quantidade_resgatada = quantidade_resgatada + 1 WHERE id_promocao = ? AND status = 'ativa' AND quantidade_resgatada < quantidade_total",
                (id_promocao,),
            )
            if cur.rowcount == 0:
                raise ErroApi("Esta recompensa esgotou.", status=400)
            codigo = novo_codigo(db)
            cur = db.execute(
                "INSERT INTO voucher (codigo, id_promocao, id_usuario, pontos_gastos, validade) VALUES (?, ?, ?, ?, ?)",
                (codigo, id_promocao, usuario["id_usuario"], custo, p["fim"]),
            )
            id_voucher = cur.lastrowid
            saldo = db.execute("SELECT saldo FROM carteira WHERE id_usuario = ?", (usuario["id_usuario"],)).fetchone()["saldo"]
            db.execute(
                """INSERT INTO movimento_pontos (id_usuario, tipo, pontos, descricao, id_loja, id_voucher, chave, saldo_apos)
                   VALUES (?, 'resgate', ?, ?, ?, ?, ?, ?)""",
                (usuario["id_usuario"], -custo, "Resgate: %s (%s)" % (p["titulo"], p["nome_fantasia"]), p["id_loja"], id_voucher, "resgate:%d" % id_voucher, saldo),
            )
            conta.notificar(p["id_logista"], "pedidos", "Voucher resgatado", "%s resgatou “%s”." % (usuario["nome"].split()[0], p["titulo"]), "minha_loja.html")
            conta.registrar_atividade(usuario["id_usuario"], "Resgatou um voucher", "%s em %s" % (p["titulo"], p["nome_fantasia"]))
            db.commit()
        except BaseException:
            db.rollback()
            raise
        return jsonify({"voucher": {"codigo": codigo, "pontos": custo, "validade": p["fim"], "titulo": p["titulo"], "loja": p["nome_fantasia"], "saldo": saldo}}), 201

    # ---------- Nordestinando+
    def plano_resposta(db, usuario):
        pl = estado_plano(db, usuario["id_usuario"])
        pl["preco_centavos"] = REGRAS["premium"]["preco_centavos"]
        pl["preco"] = "R$ %.2f" % (REGRAS["premium"]["preco_centavos"] / 100)
        pl["dias_periodo"] = REGRAS["premium"]["dias_periodo"]
        pl["demo_disponivel"] = os.environ.get("PAGAMENTO_DEMO") == "1"
        pl["pagamento_configurado"] = bool(os.environ.get("PAGAMENTO_WEBHOOK_SEGREDO"))
        return pl

    @app.get("/api/premium")
    @exigir("CLIENTE")
    def ver_premium(usuario):
        return jsonify({"plano": plano_resposta(banco.conexao(), usuario)})

    def abrir_periodo(db, id_usuario, ambiente, status_pagamento, gateway, referencia):
        """Cria/estende a assinatura e registra o pagamento. Só chamar com pagamento confirmado (ou demo identificado)."""
        dias = REGRAS["premium"]["dias_periodo"]
        ultima = db.execute("SELECT * FROM assinatura WHERE id_usuario = ? AND status = 'ativa' ORDER BY id_assinatura DESC LIMIT 1", (id_usuario,)).fetchone()
        inicio = date.today()
        if ultima is not None and ultima["fim"] >= hoje():
            inicio = date.fromisoformat(ultima["fim"])  # renovação soma ao período que ainda resta
        fim = inicio + timedelta(days=dias)
        cur = db.execute(
            "INSERT INTO assinatura (id_usuario, status, inicio, fim, valor_centavos, ambiente) VALUES (?, 'ativa', ?, ?, ?, ?)",
            (id_usuario, inicio.isoformat(), fim.isoformat(), REGRAS["premium"]["preco_centavos"], ambiente),
        )
        db.execute(
            "INSERT INTO pagamento (id_assinatura, valor_centavos, status, gateway, referencia_externa) VALUES (?, ?, ?, ?, ?)",
            (cur.lastrowid, REGRAS["premium"]["preco_centavos"], status_pagamento, gateway, referencia),
        )
        return fim.isoformat()

    @app.post("/api/premium/assinar")
    @exigir("CLIENTE")
    def assinar(usuario):
        if os.environ.get("PAGAMENTO_DEMO") != "1":
            raise ErroApi(
                "O pagamento do Nordestinando+ ainda não está configurado neste servidor. Nenhuma cobrança foi feita e a assinatura não foi ativada.",
                status=503,
            )
        db = banco.conexao()
        iniciar_escrita(db)
        fim = abrir_periodo(db, usuario["id_usuario"], "demo", "demo", "demonstracao", "demo-%s" % secrets.token_hex(8))
        conta.registrar_atividade(usuario["id_usuario"], "Assinatura Nordestinando+ (DEMONSTRAÇÃO)", "válida até %s" % fim)
        conta.notificar(usuario["id_usuario"], "seguranca", "Nordestinando+ ativado (demonstração)", "Pagamento simulado, sem cobrança real. Pontos em dobro até %s." % fim, "carteira.html")
        db.commit()
        return jsonify({"plano": plano_resposta(db, usuario)}), 201

    @app.post("/api/premium/cancelar")
    @exigir("CLIENTE")
    def cancelar_premium(usuario):
        db = banco.conexao()
        pl = estado_plano(db, usuario["id_usuario"])
        if pl["estado"] != "premium_ativo":
            raise ErroApi("Você não tem uma assinatura ativa para cancelar.", status=400)
        db.execute(
            "UPDATE assinatura SET status = 'cancelada', cancelada_em = CURRENT_TIMESTAMP WHERE id_usuario = ? AND status = 'ativa'",
            (usuario["id_usuario"],),
        )
        conta.registrar_atividade(usuario["id_usuario"], "Assinatura Nordestinando+ cancelada")
        conta.notificar(usuario["id_usuario"], "seguranca", "Nordestinando+ cancelado", "Seus pontos voltam a valer 1x. Você pode assinar de novo quando quiser.", "premium.html")
        db.commit()
        return jsonify({"plano": plano_resposta(db, usuario)})

    @app.post("/api/premium/webhook")
    def webhook_pagamento():
        """Contrato para o gateway de pagamento (a integração real ainda não existe).
        O gateway envia POST com o corpo JSON e o cabeçalho X-Assinatura = HMAC-SHA256(corpo, PAGAMENTO_WEBHOOK_SEGREDO) em hexadecimal.
        Corpo: {"id_usuario": 1, "referencia": "id-do-pagamento", "status": "confirmado", "valor_centavos": 590}"""
        segredo = os.environ.get("PAGAMENTO_WEBHOOK_SEGREDO")
        if not segredo:
            raise ErroApi("Webhook de pagamento não configurado.", status=503)
        corpo = request.get_data()
        esperado = hmac.new(segredo.encode(), corpo, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(esperado, request.headers.get("X-Assinatura", "")):
            raise ErroApi("Assinatura inválida.", status=401)
        d = dados_json()
        db = banco.conexao()
        if d.get("status") != "confirmado" or d.get("valor_centavos") != REGRAS["premium"]["preco_centavos"] or not d.get("referencia"):
            raise ErroApi("Pagamento não confirmado.", status=400)
        if db.execute("SELECT 1 FROM pagamento WHERE referencia_externa = ?", (str(d["referencia"]),)).fetchone():
            return jsonify({"ok": True, "repetido": True})  # o gateway reenviou: não cobra nem estende de novo
        if not db.execute("SELECT 1 FROM usuario WHERE id_usuario = ? AND perfil = 'CLIENTE'", (d.get("id_usuario"),)).fetchone():
            raise ErroApi("Usuário não encontrado.", status=404)
        iniciar_escrita(db)
        fim = abrir_periodo(db, d["id_usuario"], "producao", "confirmado", "gateway", str(d["referencia"]))
        conta.notificar(d["id_usuario"], "seguranca", "Nordestinando+ ativo", "Pagamento confirmado. Pontos em dobro até %s." % fim, "carteira.html")
        db.commit()
        return jsonify({"ok": True})

    # ---------- avaliações com pontos (usada pelo app.py)
    # ---------- painel do comerciante: promoções
    def loja_do(usuario):
        l = banco.conexao().execute("SELECT * FROM loja WHERE id_logista = ?", (usuario["id_usuario"],)).fetchone()
        if l is None:
            raise ErroApi("Loja não encontrada.", status=404)
        return l

    def validar_promocao(d, existente=None):
        erros = {}
        titulo = texto(d, "titulo", 80)
        descricao = texto(d, "descricao", 300)
        tipo = d.get("tipo_beneficio")
        condicoes = texto(d, "condicoes", 500)
        if len(titulo) < 3:
            erros["titulo"] = "Dê um nome para a promoção."
        if len(descricao) < 5:
            erros["descricao"] = "Descreva a oferta."
        if tipo not in TIPOS_BENEFICIO:
            erros["tipo_beneficio"] = "Escolha o tipo de benefício."
        valor = None
        if tipo in ("percentual", "valor_fixo"):
            try:
                valor = float(str(d.get("valor_beneficio")).replace(",", "."))
                assert valor > 0 and (tipo != "percentual" or valor <= 100)
            except (TypeError, ValueError, AssertionError):
                erros["valor_beneficio"] = "Informe um percentual de 1 a 100." if tipo == "percentual" else "Informe o valor do desconto."
        try:
            pontos = int(d.get("pontos_necessarios"))
            assert 1 <= pontos <= 100000
        except (TypeError, ValueError, AssertionError):
            erros["pontos_necessarios"] = "Informe quantos pontos (1 a 100000)."
            pontos = None
        try:
            qtd = int(d.get("quantidade_total"))
            assert 1 <= qtd <= 100000
        except (TypeError, ValueError, AssertionError):
            erros["quantidade_total"] = "Informe quantos vouchers estarão disponíveis."
            qtd = None
        try:
            limite = int(d.get("limite_por_usuario") or 1)
            assert 1 <= limite <= 20
        except (TypeError, ValueError, AssertionError):
            erros["limite_por_usuario"] = "Use de 1 a 20."
            limite = 1
        try:
            inicio = date.fromisoformat(str(d.get("inicio")))
            fim = date.fromisoformat(str(d.get("fim")))
            if fim < inicio:
                erros["fim"] = "O encerramento não pode ser antes do início."
            elif fim < date.today():
                erros["fim"] = "O encerramento precisa ser hoje ou depois."
        except ValueError:
            erros["inicio"] = "Informe as datas de início e encerramento."
            inicio = fim = None
        if erros:
            raise ErroApi("Corrija os campos destacados.", erros)
        return dict(titulo=titulo, descricao=descricao, tipo_beneficio=tipo, valor_beneficio=valor, pontos_necessarios=pontos,
                    quantidade_total=qtd, limite_por_usuario=limite, inicio=inicio.isoformat(), fim=fim.isoformat(), condicoes=condicoes)

    def promocao_painel(db, p):
        cont = db.execute(
            """SELECT COUNT(*) AS total,
                      COALESCE(SUM(status = 'utilizado'), 0) AS utilizados,
                      COALESCE(SUM(status = 'cancelado'), 0) AS cancelados,
                      COALESCE(SUM(status = 'resgatado' AND validade >= ?), 0) AS disponiveis,
                      COALESCE(SUM(status = 'resgatado' AND validade < ?), 0) AS expirados
               FROM voucher WHERE id_promocao = ?""",
            (hoje(), hoje(), p["id_promocao"]),
        ).fetchone()
        saida = promocao_dict(p, {"id_loja": p["id_loja"], "nome_fantasia": "", "logo": None, "foto": None, "bairro": ""})
        saida.pop("loja")
        saida.update(
            {
                "status": p["status"],
                "quantidade_total": p["quantidade_total"],
                "resgatados": p["quantidade_resgatada"],
                "utilizados": cont["utilizados"], "cancelados": cont["cancelados"], "disponiveis": cont["disponiveis"], "expirados": cont["expirados"],
                "vigente": p["inicio"] <= hoje() <= p["fim"],
            }
        )
        return saida

    @app.get("/api/minha-loja/promocoes")
    @exigir("LOGISTA")
    def minhas_promocoes(usuario):
        db = banco.conexao()
        loja = loja_do(usuario)
        linhas = db.execute("SELECT * FROM promocao WHERE id_loja = ? ORDER BY id_promocao DESC", (loja["id_loja"],)).fetchall()
        return jsonify({"promocoes": [promocao_painel(db, p) for p in linhas]})

    @app.post("/api/minha-loja/promocoes")
    @exigir("LOGISTA")
    def criar_promocao(usuario):
        loja = loja_do(usuario)
        v = validar_promocao(dados_json())
        db = banco.conexao()
        cur = db.execute(
            """INSERT INTO promocao (id_loja, titulo, descricao, tipo_beneficio, valor_beneficio, pontos_necessarios, quantidade_total, limite_por_usuario, inicio, fim, condicoes)
               VALUES (:id_loja, :titulo, :descricao, :tipo_beneficio, :valor_beneficio, :pontos_necessarios, :quantidade_total, :limite_por_usuario, :inicio, :fim, :condicoes)""",
            dict(v, id_loja=loja["id_loja"]),
        )
        db.commit()
        p = db.execute("SELECT * FROM promocao WHERE id_promocao = ?", (cur.lastrowid,)).fetchone()
        return jsonify({"promocao": promocao_painel(db, p)}), 201

    @app.patch("/api/minha-loja/promocoes/<int:id_promocao>")
    @exigir("LOGISTA")
    def editar_promocao(usuario, id_promocao):
        loja = loja_do(usuario)
        db = banco.conexao()
        p = db.execute("SELECT * FROM promocao WHERE id_promocao = ? AND id_loja = ?", (id_promocao, loja["id_loja"])).fetchone()
        if p is None:
            raise ErroApi("Promoção não encontrada.", status=404)
        d = dados_json()
        if set(d.keys()) <= {"status"}:  # só mudar o estado: ativar, pausar ou encerrar
            novo = d.get("status")
            if novo not in ("ativa", "pausada", "encerrada"):
                raise ErroApi("Estado inválido.")
            if p["status"] == "encerrada":
                raise ErroApi("Uma promoção encerrada não pode ser reaberta. Crie uma nova.", status=400)
            db.execute("UPDATE promocao SET status = ? WHERE id_promocao = ?", (novo, id_promocao))
        else:
            if p["status"] == "encerrada":
                raise ErroApi("Uma promoção encerrada não pode ser editada.", status=400)
            v = validar_promocao(dict({k: p[k] for k in p.keys()}, **d))
            if p["quantidade_resgatada"] > 0:
                if v["pontos_necessarios"] != p["pontos_necessarios"] or v["tipo_beneficio"] != p["tipo_beneficio"] or v["valor_beneficio"] != p["valor_beneficio"]:
                    raise ErroApi("Já existem vouchers resgatados: o benefício e os pontos não podem mais mudar.", {"pontos_necessarios": "Bloqueado: já há resgates."})
                if v["quantidade_total"] < p["quantidade_resgatada"]:
                    raise ErroApi("A quantidade não pode ser menor que os vouchers já resgatados.", {"quantidade_total": "Mínimo: %d." % p["quantidade_resgatada"]})
            db.execute(
                """UPDATE promocao SET titulo = :titulo, descricao = :descricao, tipo_beneficio = :tipo_beneficio, valor_beneficio = :valor_beneficio,
                   pontos_necessarios = :pontos_necessarios, quantidade_total = :quantidade_total, limite_por_usuario = :limite_por_usuario,
                   inicio = :inicio, fim = :fim, condicoes = :condicoes WHERE id_promocao = :id""",
                dict(v, id=id_promocao),
            )
        db.commit()
        p = db.execute("SELECT * FROM promocao WHERE id_promocao = ?", (id_promocao,)).fetchone()
        return jsonify({"promocao": promocao_painel(db, p)})

    @app.get("/api/minha-loja/vouchers")
    @exigir("LOGISTA")
    def vouchers_da_loja(usuario):
        loja = loja_do(usuario)
        db = banco.conexao()
        linhas = db.execute(
            """SELECT v.*, p.titulo, p.tipo_beneficio, p.valor_beneficio, u.nome AS cliente
               FROM voucher v JOIN promocao p ON p.id_promocao = v.id_promocao JOIN usuario u ON u.id_usuario = v.id_usuario
               WHERE p.id_loja = ? ORDER BY v.id_voucher DESC LIMIT 200""",
            (loja["id_loja"],),
        ).fetchall()
        saida = []
        for v in linhas:
            est = estado_voucher(v)
            saida.append({"id": v["id_voucher"], "codigo": v["codigo"], "estado": est, "estado_rotulo": ROTULO_ESTADO[est], "titulo": v["titulo"],
                          "beneficio": descricao_beneficio(v), "cliente": v["cliente"].split()[0], "validade": v["validade"],
                          "resgatado_em": v["resgatado_em"], "utilizado_em": v["utilizado_em"], "pontos": v["pontos_gastos"]})
        return jsonify({"vouchers": saida})

    def limitar_tentativas(usuario):
        chave = "u%d" % usuario["id_usuario"]
        if conta.tentativas_recentes("voucher", chave, 600) >= 20:
            raise ErroApi("Muitas tentativas com códigos errados. Aguarde alguns minutos.", status=429)
        return chave

    def achar_voucher(db, loja, codigo, usuario):
        chave = limitar_tentativas(usuario)
        codigo = re.sub(r"[^A-Za-z0-9-]", "", codigo or "").upper()
        v = db.execute(
            """SELECT v.*, p.titulo, p.tipo_beneficio, p.valor_beneficio, p.id_loja, u.nome AS cliente
               FROM voucher v JOIN promocao p ON p.id_promocao = v.id_promocao JOIN usuario u ON u.id_usuario = v.id_usuario WHERE v.codigo = ?""",
            (codigo,),
        ).fetchone()
        if v is None or v["id_loja"] != loja["id_loja"]:
            conta.registrar_tentativa("voucher", chave)
            raise ErroApi("Código não encontrado nesta loja.", status=404)
        return v

    def voucher_loja_dict(v):
        est = estado_voucher(v)
        return {"id": v["id_voucher"], "codigo": v["codigo"], "estado": est, "estado_rotulo": ROTULO_ESTADO[est], "titulo": v["titulo"],
                "beneficio": descricao_beneficio(v), "cliente": v["cliente"].split()[0], "validade": v["validade"], "utilizado_em": v["utilizado_em"]}

    @app.get("/api/minha-loja/vouchers/consultar")
    @exigir("LOGISTA")
    def consultar_voucher(usuario):
        v = achar_voucher(banco.conexao(), loja_do(usuario), request.args.get("codigo"), usuario)
        return jsonify({"voucher": voucher_loja_dict(v)})

    @app.post("/api/minha-loja/vouchers/validar")
    @exigir("LOGISTA")
    def validar_voucher(usuario):
        db = banco.conexao()
        loja = loja_do(usuario)
        v = achar_voucher(db, loja, dados_json().get("codigo"), usuario)
        est = estado_voucher(v)
        if est == "utilizado":
            raise ErroApi("Este voucher já foi utilizado em %s." % (v["utilizado_em"] or ""), status=409)
        if est == "cancelado":
            raise ErroApi("Este voucher foi cancelado.", status=400)
        if est == "expirado":
            raise ErroApi("Este voucher expirou em %s." % v["validade"], status=400)
        iniciar_escrita(db)
        cur = db.execute(
            "UPDATE voucher SET status = 'utilizado', utilizado_em = CURRENT_TIMESTAMP, validado_por = ? WHERE id_voucher = ? AND status = 'resgatado'",
            (usuario["id_usuario"], v["id_voucher"]),
        )
        if cur.rowcount == 0:  # alguém validou no mesmo instante
            db.rollback()
            raise ErroApi("Este voucher já foi utilizado.", status=409)
        conta.notificar(v["id_usuario"], "pedidos", "Voucher utilizado", "Seu voucher “%s” foi validado em %s." % (v["titulo"], loja["nome_fantasia"]), "carteira.html")
        db.commit()
        v = db.execute(
            """SELECT v.*, p.titulo, p.tipo_beneficio, p.valor_beneficio, u.nome AS cliente FROM voucher v JOIN promocao p ON p.id_promocao = v.id_promocao
               JOIN usuario u ON u.id_usuario = v.id_usuario WHERE v.id_voucher = ?""",
            (v["id_voucher"],),
        ).fetchone()
        return jsonify({"voucher": voucher_loja_dict(v)})

    @app.post("/api/minha-loja/vouchers/<int:id_voucher>/cancelar")
    @exigir("LOGISTA")
    def cancelar_voucher(usuario, id_voucher):
        db = banco.conexao()
        loja = loja_do(usuario)
        v = db.execute(
            "SELECT v.*, p.titulo, p.id_loja FROM voucher v JOIN promocao p ON p.id_promocao = v.id_promocao WHERE v.id_voucher = ? AND p.id_loja = ?",
            (id_voucher, loja["id_loja"]),
        ).fetchone()
        if v is None:
            raise ErroApi("Voucher não encontrado.", status=404)
        iniciar_escrita(db)
        cur = db.execute("UPDATE voucher SET status = 'cancelado' WHERE id_voucher = ? AND status = 'resgatado'", (id_voucher,))
        if cur.rowcount == 0:
            db.rollback()
            raise ErroApi("Só dá para cancelar vouchers que ainda não foram utilizados.", status=400)
        # devolve os pontos ao cliente (uma única vez: a chave do estorno é única)
        garantir_carteira(db, v["id_usuario"])
        db.execute("UPDATE carteira SET saldo = saldo + ?, total_usado = total_usado - ? WHERE id_usuario = ?", (v["pontos_gastos"], v["pontos_gastos"], v["id_usuario"]))
        saldo = db.execute("SELECT saldo FROM carteira WHERE id_usuario = ?", (v["id_usuario"],)).fetchone()["saldo"]
        db.execute(
            "INSERT INTO movimento_pontos (id_usuario, tipo, pontos, descricao, id_loja, id_voucher, chave, saldo_apos) VALUES (?, 'estorno', ?, ?, ?, ?, ?, ?)",
            (v["id_usuario"], v["pontos_gastos"], "Estorno: voucher cancelado (%s)" % v["titulo"], loja["id_loja"], id_voucher, "estorno:%d" % id_voucher, saldo),
        )
        conta.notificar(v["id_usuario"], "pedidos", "Voucher cancelado", "Seu voucher “%s” foi cancelado e seus %d pontos voltaram para a carteira." % (v["titulo"], v["pontos_gastos"]), "carteira.html")
        db.commit()
        return jsonify({"ok": True})

    # ---------- indicadores para a equipe do Nordestinando
    @app.get("/api/admin/gamificacao")
    def indicadores():
        token = os.environ.get("ADMIN_TOKEN")
        if not token:
            raise ErroApi("Painel administrativo não configurado (defina ADMIN_TOKEN no .env).", status=503)
        if not hmac.compare_digest(token, request.headers.get("X-Admin-Token", "")):
            raise ErroApi("Acesso negado.", status=403)
        db = banco.conexao()
        um = lambda sql, *a: db.execute(sql, a).fetchone()[0]
        premium = db.execute(
            """SELECT COUNT(DISTINCT id_usuario) FROM assinatura a WHERE status = 'ativa' AND fim >= ?
               AND id_assinatura = (SELECT MAX(id_assinatura) FROM assinatura WHERE id_usuario = a.id_usuario)""",
            (hoje(),),
        ).fetchone()[0]
        top = db.execute(
            """SELECT l.nome_fantasia AS loja, COUNT(v.id_voucher) AS resgates, COALESCE(SUM(v.status = 'utilizado'), 0) AS utilizados
               FROM promocao p JOIN loja l ON l.id_loja = p.id_loja LEFT JOIN voucher v ON v.id_promocao = p.id_promocao
               GROUP BY l.id_loja ORDER BY resgates DESC, utilizados DESC LIMIT 5"""
        ).fetchall()
        return jsonify(
            {
                "pontos_distribuidos": um("SELECT COALESCE(SUM(pontos), 0) FROM movimento_pontos WHERE tipo = 'avaliacao'"),
                "pontos_bonus_premium": um("SELECT COALESCE(SUM(pontos_bonus), 0) FROM movimento_pontos WHERE tipo = 'avaliacao'"),
                "pontos_resgatados": um("SELECT COALESCE(-SUM(pontos), 0) FROM movimento_pontos WHERE tipo = 'resgate'"),
                "usuarios_premium": premium,
                "receita_assinaturas_centavos": um("SELECT COALESCE(SUM(valor_centavos), 0) FROM pagamento WHERE status = 'confirmado'"),
                "pagamentos_demo": um("SELECT COUNT(*) FROM pagamento WHERE status = 'demo'"),
                "promocoes_criadas": um("SELECT COUNT(*) FROM promocao"),
                "vouchers_emitidos": um("SELECT COUNT(*) FROM voucher"),
                "vouchers_utilizados": um("SELECT COUNT(*) FROM voucher WHERE status = 'utilizado'"),
                "lojas_com_mais_adesao": [dict(t) for t in top],
            }
        )
