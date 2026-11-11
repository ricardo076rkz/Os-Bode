"""Nordestinando - servidor (Flask).

Rodar:  python python/app.py   e abrir  http://localhost:5000
O mesmo servidor entrega as telas (html/js/style) e a API (/api/...).
"""
import json
import os
import re
import secrets
import sqlite3
from datetime import timedelta
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory, session
from werkzeug.security import check_password_hash, generate_password_hash

PASTA = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(PASTA)
load_dotenv(os.path.join(RAIZ, ".env"))

import banco  # noqa: E402  (precisa vir depois do load_dotenv por causa do DB_PATH)
import agenda  # noqa: E402
import conta  # noqa: E402
import gamificacao  # noqa: E402
import lgpd  # noqa: E402

app = Flask(__name__, static_folder=None)


def chave_secreta():
    # SECRET_KEY do .env; se não tiver, cria uma e guarda em python/.secret_key
    do_env = os.environ.get("SECRET_KEY")
    if do_env:
        return do_env
    caminho = os.path.join(PASTA, ".secret_key")
    if os.path.exists(caminho):
        with open(caminho) as f:
            return f.read().strip()
    nova = secrets.token_hex(32)
    with open(caminho, "w") as f:
        f.write(nova)
    return nova


app.config.update(
    SECRET_KEY=chave_secreta(),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SEGURO") == "1",  # ligue só com HTTPS
    PERMANENT_SESSION_LIFETIME=timedelta(days=conta.MAX_SESSAO_DIAS),
    MAX_CONTENT_LENGTH=6 * 1024 * 1024,
)
app.teardown_appcontext(banco.fechar)
banco.criar_tabelas()
agenda.semear()

DIAS = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]
DIAS_EVENTO = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
SEGMENTOS = ["Alimentação", "Cafeteria", "Artesanato", "Souvenirs", "Vestuário", "Serviços", "Outros"]
MAX_IMAGEM = 900_000  # caracteres do data URL


# ---------------------------------------------------------------- utilidades
class ErroApi(Exception):
    def __init__(self, mensagem, campos=None, status=400):
        self.mensagem = mensagem
        self.campos = campos or {}
        self.status = status


@app.errorhandler(ErroApi)
def tratar_erro(e):
    return jsonify({"erro": e.mensagem, "campos": e.campos}), e.status


@app.errorhandler(413)
def muito_grande(e):
    return jsonify({"erro": "Arquivo grande demais.", "campos": {}}), 413


@app.errorhandler(404)
def nao_achou(e):
    if request.path.startswith("/api/"):
        return jsonify({"erro": "Não encontrado.", "campos": {}}), 404
    return "Página não encontrada", 404


def dados_json():
    corpo = request.get_json(silent=True)
    if not isinstance(corpo, dict):
        raise ErroApi("Envie os dados em JSON.")
    return corpo


def texto(d, chave, maximo=200):
    valor = d.get(chave)
    if valor is None:
        return ""
    return str(valor).strip()[:maximo]


def so_digitos(s):
    return re.sub(r"\D", "", s or "")


def cnpj_valido(cnpj):
    c = so_digitos(cnpj)
    if len(c) != 14 or c == c[0] * 14:
        return False

    def digito(base, pesos):
        resto = sum(int(n) * p for n, p in zip(base, pesos)) % 11
        return "0" if resto < 2 else str(11 - resto)

    p1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    p2 = [6] + p1
    return c[12] == digito(c[:12], p1) and c[13] == digito(c[:13], p2)


def imagem_valida(valor):
    if not valor:
        return ""
    if not isinstance(valor, str) or not re.match(r"^data:image/(jpeg|png|webp);base64,[A-Za-z0-9+/=]+$", valor):
        raise ErroApi("Imagem inválida.")
    if len(valor) > MAX_IMAGEM:
        raise ErroApi("Imagem grande demais. Use uma foto menor.")
    return valor


def usuario_logado():
    id_usuario = conta.id_usuario_da_sessao()
    if not id_usuario:
        return None
    return banco.conexao().execute("SELECT * FROM usuario WHERE id_usuario = ?", (id_usuario,)).fetchone()


def exigir(perfil=None):
    def decorador(funcao):
        @wraps(funcao)
        def interno(*args, **kwargs):
            usuario = usuario_logado()
            if usuario is None:
                raise ErroApi("Faça login para continuar.", status=401)
            if perfil and usuario["perfil"] != perfil:
                raise ErroApi("Seu perfil não tem permissão para isso.", status=403)
            return funcao(usuario, *args, **kwargs)

        return interno

    return decorador


# ---------------------------------------------------------------- validações
def validar_conta(d, erros):
    nome = texto(d, "nome", 100)
    email = texto(d, "email", 150).lower()
    telefone = so_digitos(texto(d, "telefone", 20))
    senha = str(d.get("senha") or "")
    confirmar = str(d.get("confirmar_senha") or "")

    if len(nome) < 3:
        erros["nome"] = "Informe o nome completo."
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        erros["email"] = "E-mail inválido."
    if len(telefone) not in (10, 11):
        erros["telefone"] = "Telefone com DDD, 10 ou 11 dígitos."
    validar_senha_nova(senha, confirmar, erros)
    return nome, email, telefone, senha


def validar_senha_nova(senha, confirmar, erros):
    if len(senha) < 8:
        erros["senha"] = "A senha precisa ter pelo menos 8 caracteres."
    elif not (re.search(r"[A-Za-z]", senha) and re.search(r"\d", senha)):
        erros["senha"] = "Use letras e números na senha."
    if senha != confirmar:
        erros["confirmar_senha"] = "As senhas não são iguais."


def validar_horarios(horarios, erros):
    if not isinstance(horarios, dict):
        erros["horarios"] = "Informe os horários de funcionamento."
        return {}
    limpo = {}
    algum_aberto = False
    for dia in DIAS:
        h = horarios.get(dia) or {}
        fechado = bool(h.get("fechado"))
        abre, fecha = str(h.get("abre") or ""), str(h.get("fecha") or "")
        if not fechado:
            if not (re.match(r"^\d{2}:\d{2}$", abre) and re.match(r"^\d{2}:\d{2}$", fecha)) or abre >= fecha:
                erros["horarios"] = "Confira os horários: a abertura deve ser antes do fechamento."
                return {}
            algum_aberto = True
        limpo[dia] = {"fechado": fechado, "abre": abre, "fecha": fecha}
    if not algum_aberto:
        erros["horarios"] = "A loja precisa abrir em pelo menos um dia."
    return limpo


def validar_loja(d, erros):
    loja = {
        "nome_fantasia": texto(d, "nome_fantasia", 100),
        "segmento": texto(d, "segmento", 50),
        "descricao": texto(d, "descricao", 500),
        "cep": so_digitos(texto(d, "cep", 10)),
        "rua": texto(d, "rua", 150),
        "numero": texto(d, "numero", 20),
        "bairro": texto(d, "bairro", 100),
        "cidade": texto(d, "cidade", 100),
        "estado": texto(d, "estado", 2).upper(),
        "telefone": so_digitos(texto(d, "telefone_comercial", 20)),
        "whatsapp": so_digitos(texto(d, "whatsapp", 20)),
        "instagram": texto(d, "instagram", 60).lstrip("@"),
        "site": texto(d, "site", 200),
    }
    if len(loja["nome_fantasia"]) < 2:
        erros["nome_fantasia"] = "Informe o nome fantasia."
    if loja["segmento"] not in SEGMENTOS:
        erros["segmento"] = "Escolha um segmento."
    if len(loja["descricao"]) < 10:
        erros["descricao"] = "Descreva o estabelecimento (mínimo 10 caracteres)."
    if len(loja["cep"]) != 8:
        erros["cep"] = "CEP com 8 dígitos."
    for campo, rotulo in (("rua", "a rua"), ("numero", "o número"), ("bairro", "o bairro"), ("cidade", "a cidade")):
        if not loja[campo]:
            erros[campo] = "Informe " + rotulo + "."
    if not re.match(r"^[A-Z]{2}$", loja["estado"]):
        erros["estado"] = "Use a sigla do estado (ex.: PE)."
    if len(loja["telefone"]) not in (10, 11):
        erros["telefone_comercial"] = "Telefone comercial com DDD."
    if loja["whatsapp"] and len(loja["whatsapp"]) not in (10, 11):
        erros["whatsapp"] = "WhatsApp com DDD."
    if loja["site"] and not re.match(r"^https?://", loja["site"]):
        erros["site"] = "O site deve começar com http:// ou https://"

    try:
        loja["latitude"] = float(d.get("latitude"))
        loja["longitude"] = float(d.get("longitude"))
        if not (-90 <= loja["latitude"] <= 90 and -180 <= loja["longitude"] <= 180):
            raise ValueError
    except (TypeError, ValueError):
        erros["latitude"] = "Marque a localização da loja no mapa (ou informe latitude e longitude)."
        loja["latitude"] = loja["longitude"] = 0

    loja["horarios"] = json.dumps(validar_horarios(d.get("horarios"), erros))
    loja["logo"] = imagem_valida(d.get("logo"))
    loja["foto"] = imagem_valida(d.get("foto"))
    return loja


def validar_cnpj_opcional(d, erros):
    cnpj = so_digitos(texto(d, "cnpj", 20))
    razao = texto(d, "razao_social", 150)
    if cnpj and not cnpj_valido(cnpj):
        erros["cnpj"] = "CNPJ inválido."
    if cnpj and not razao:
        erros["razao_social"] = "Informe a razão social do CNPJ."
    return (cnpj or None), razao


# ---------------------------------------------------------------- conversão
def loja_para_dict(linha, completo=True):
    db = banco.conexao()
    nota = db.execute(
        "SELECT AVG(nota) AS media, COUNT(*) AS total FROM avaliacao WHERE id_loja = ?", (linha["id_loja"],)
    ).fetchone()
    saida = {
        "id": linha["id_loja"],
        "nome": linha["nome_fantasia"],
        "segmento": linha["segmento"],
        "descricao": linha["descricao"],
        "endereco": "%s, %s - %s, %s/%s" % (linha["rua"], linha["numero"], linha["bairro"], linha["cidade"], linha["estado"]),
        "latitude": linha["latitude"],
        "longitude": linha["longitude"],
        "nota": round(nota["media"], 1) if nota["media"] else None,
        "total_avaliacoes": nota["total"],
        "telefone": linha["telefone"],
        "whatsapp": linha["whatsapp"],
        "instagram": linha["instagram"],
        "site": linha["site"],
        "horarios": json.loads(linha["horarios"]),
        "logo": linha["logo"],
        "foto": linha["foto"],
        "itens": [
            {"id": i["id_item"], "nome": i["nome"], "valor": i["valor"], "foto": i["foto"]}
            for i in db.execute("SELECT * FROM item_vitrine WHERE id_loja = ? ORDER BY id_item", (linha["id_loja"],))
        ],
    }
    if completo:
        saida.update(
            {k: linha[k] for k in ("cep", "rua", "numero", "bairro", "cidade", "estado")}
        )
    return saida


def evento_para_dict(e):
    return {
        "id": e["id_evento"],
        "id_loja": e["id_loja"],
        "nome": e["nome"],
        "dia": e["dia_semana"],
        "horario": e["horario"],
        "descricao": e["descricao"],
        "latitude": e["latitude"],
        "longitude": e["longitude"],
        "loja": e["nome_fantasia"] if "nome_fantasia" in e.keys() else None,
    }


def usuario_para_dict(u):
    return {"id": u["id_usuario"], "nome": u["nome"], "email": u["email"], "perfil": u["perfil"]}


# ---------------------------------------------------------------- páginas
@app.route("/")
def inicio():
    return send_from_directory(RAIZ, "index.html")


@app.route("/manifest.webmanifest")
def manifesto():
    return send_from_directory(RAIZ, "manifest.webmanifest", mimetype="application/manifest+json")


@app.route("/<path:caminho>")
def arquivos(caminho):
    # só entrega as pastas do site (nunca python/, sql/, .env, .git...)
    topo = caminho.split("/")[0]
    if caminho != "index.html" and topo not in ("html", "js", "style"):
        return "Página não encontrada", 404
    return send_from_directory(RAIZ, caminho)


@app.before_request
def limpeza_periodica():
    lgpd.limpar_se_preciso()


@app.after_request
def cabecalhos(resp):
    if request.path.startswith("/api/"):
        resp.headers["Cache-Control"] = "no-store"  # dados da conta nunca ficam em cache
    else:
        resp.headers["Cache-Control"] = "no-cache"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Permissions-Policy"] = "camera=(), microphone=(), payment=(), geolocation=(self)"
    if os.environ.get("COOKIE_SEGURO") == "1":
        resp.headers["Strict-Transport-Security"] = "max-age=31536000"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"  # o OpenStreetMap exige o Referer nos mapas
    return resp


# ---------------------------------------------------------------- configuração e conta
@app.get("/api/config")
def config():
    return jsonify({"segmentos": SEGMENTOS})


@app.get("/api/eu")
def eu():
    u = usuario_logado()
    return jsonify({"usuario": usuario_para_dict(u) if u else None})


@app.post("/api/cadastro/usuario")
def cadastro_usuario():
    d = dados_json()
    erros = {}
    nome, email, telefone, senha = validar_conta(d, erros)
    lgpd.exigir_aceite(d, erros)
    if erros:
        raise ErroApi("Corrija os campos destacados.", erros)
    db = banco.conexao()
    try:
        cur = db.execute(
            "INSERT INTO usuario (nome, email, telefone, senha_hash, perfil) VALUES (?, ?, ?, ?, 'CLIENTE')",
            (nome, email, telefone, generate_password_hash(senha)),
        )
        lgpd.registrar_aceite(cur.lastrowid)
        db.commit()
    except sqlite3.IntegrityError:
        raise ErroApi("Corrija os campos destacados.", {"email": "Este e-mail já está cadastrado."})
    conta.iniciar_sessao(cur.lastrowid)
    conta.registrar_atividade(cur.lastrowid, "Conta criada")
    conta.notificar(cur.lastrowid, "seguranca", "Bem-vindo ao Nordestinando", "Sua conta foi criada. Explore as lojas de Caruaru e avalie as que você visitar.", "explorar.html")
    db.commit()
    return jsonify({"usuario": usuario_para_dict(usuario_logado())}), 201


@app.post("/api/cadastro/comerciante")
def cadastro_comerciante():
    d = dados_json()
    erros = {}
    nome, email, telefone, senha = validar_conta(d, erros)
    cnpj, razao = validar_cnpj_opcional(d, erros)
    loja = validar_loja(d, erros)
    lgpd.exigir_aceite(d, erros)
    if erros:
        raise ErroApi("Corrija os campos destacados.", erros)

    db = banco.conexao()
    try:
        cur = db.execute(
            "INSERT INTO usuario (nome, email, telefone, senha_hash, perfil) VALUES (?, ?, ?, ?, 'LOGISTA')",
            (nome, email, telefone, generate_password_hash(senha)),
        )
        id_usuario = cur.lastrowid
        db.execute("INSERT INTO logista (id_usuario, cnpj, razao_social) VALUES (?, ?, ?)", (id_usuario, cnpj, razao))
        db.execute(
            """INSERT INTO loja (id_logista, nome_fantasia, segmento, descricao, cep, rua, numero, bairro,
                                 cidade, estado, latitude, longitude, horarios, telefone, whatsapp,
                                 instagram, site, logo, foto)
               VALUES (:id, :nome_fantasia, :segmento, :descricao, :cep, :rua, :numero, :bairro, :cidade,
                       :estado, :latitude, :longitude, :horarios, :telefone, :whatsapp, :instagram,
                       :site, :logo, :foto)""",
            dict(loja, id=id_usuario),
        )
        lgpd.registrar_aceite(id_usuario)
        db.commit()
    except sqlite3.IntegrityError as e:
        db.rollback()
        if "usuario.email" in str(e):
            raise ErroApi("Corrija os campos destacados.", {"email": "Este e-mail já está cadastrado."})
        if "logista.cnpj" in str(e):
            raise ErroApi("Corrija os campos destacados.", {"cnpj": "Este CNPJ já está cadastrado."})
        raise ErroApi("Não foi possível salvar o cadastro.")
    conta.iniciar_sessao(id_usuario)
    conta.registrar_atividade(id_usuario, "Conta de comerciante criada")
    conta.notificar(id_usuario, "seguranca", "Loja cadastrada", "Sua loja já aparece no mapa. Adicione produtos na vitrine e anuncie eventos.", "minha_loja.html")
    db.commit()
    return jsonify({"usuario": usuario_para_dict(usuario_logado())}), 201


@app.post("/api/login")
def login():
    d = dados_json()
    email = texto(d, "email", 150).lower()
    senha = str(d.get("senha") or "")
    esperado = texto(d, "perfil", 10).upper()  # CLIENTE ou LOGISTA (o que a pessoa escolheu na tela)
    chave = email + "|" + (request.remote_addr or "?")
    maximo, janela = conta.LIMITE_LOGIN
    if conta.tentativas_recentes("login", chave, janela) >= maximo:
        raise ErroApi("Muitas tentativas erradas. Aguarde alguns minutos e tente de novo, ou use “Esqueci minha senha”.", status=429)
    u = banco.conexao().execute("SELECT * FROM usuario WHERE email = ?", (email,)).fetchone()
    if u is None or not check_password_hash(u["senha_hash"], senha):
        conta.registrar_tentativa("login", chave)
        raise ErroApi("E-mail ou senha incorretos.", status=401)
    if esperado in ("CLIENTE", "LOGISTA") and u["perfil"] != esperado:
        quem = "comerciante" if u["perfil"] == "LOGISTA" else "usuário"
        raise ErroApi("Essa conta é de %s. Troque a opção acima." % quem, status=403)
    conta.limpar_tentativas("login", chave)
    conta.iniciar_sessao(u["id_usuario"])
    conta.registrar_atividade(u["id_usuario"], "Login", conta._descrever_agente(request.headers.get("User-Agent")))
    banco.conexao().commit()
    return jsonify({"usuario": usuario_para_dict(u)})


@app.post("/api/logout")
def logout():
    conta.encerrar_sessao_atual()
    return jsonify({"ok": True})


# ---------------------------------------------------------------- público: lojas e eventos
@app.get("/api/lojas")
def listar_lojas():
    busca = "%" + texto(request.args, "q", 60).lower() + "%"
    segmento = texto(request.args, "segmento", 50)
    sql = "SELECT * FROM loja WHERE (lower(nome_fantasia) LIKE ? OR lower(descricao) LIKE ?)"
    params = [busca, busca]
    if segmento:
        sql += " AND segmento = ?"
        params.append(segmento)
    linhas = banco.conexao().execute(sql + " ORDER BY nome_fantasia", params).fetchall()
    return jsonify({"lojas": [loja_para_dict(l, completo=False) for l in linhas]})


@app.get("/api/eventos")
def listar_eventos():
    linhas = banco.conexao().execute(
        """SELECT e.*, l.nome_fantasia, l.latitude AS lat_loja, l.longitude AS lng_loja
           FROM evento e JOIN loja l ON l.id_loja = e.id_loja ORDER BY e.id_evento DESC"""
    ).fetchall()
    saida = []
    for e in linhas:
        item = evento_para_dict(e)
        item["latitude"] = e["latitude"] if e["latitude"] is not None else e["lat_loja"]
        item["longitude"] = e["longitude"] if e["longitude"] is not None else e["lng_loja"]
        saida.append(item)
    return jsonify({"eventos": saida})


@app.get("/api/lojas/<int:id_loja>/avaliacoes")
def avaliacoes_da_loja(id_loja):
    linhas = banco.conexao().execute(
        """SELECT a.*, u.nome, u.preferencias FROM avaliacao a JOIN usuario u ON u.id_usuario = a.id_cliente
           WHERE a.id_loja = ? ORDER BY a.id_avaliacao DESC""",
        (id_loja,),
    ).fetchall()
    return jsonify({"avaliacoes": [avaliacao_para_dict(a) for a in linhas]})


def avaliacao_para_dict(a):
    anonimo = not conta.preferencias_de(a)["privacidade"]["nome_nas_avaliacoes"]
    primeiro = "Anônimo" if anonimo else a["nome"].split()[0]
    return {"cliente": primeiro, "nota": a["nota"], "comentario": a["comentario"], "data": a["data_criacao"]}


# ---------------------------------------------------------------- usuário (CLIENTE)
@app.post("/api/lojas/<int:id_loja>/avaliacoes")
@exigir("CLIENTE")
def avaliar(usuario, id_loja):
    d = dados_json()
    try:
        nota = int(d.get("nota"))
        assert 1 <= nota <= 5
    except (TypeError, ValueError, AssertionError):
        raise ErroApi("Escolha uma nota de 1 a 5.", {"nota": "Escolha uma nota de 1 a 5."})
    db = banco.conexao()
    if not db.execute("SELECT 1 FROM loja WHERE id_loja = ?", (id_loja,)).fetchone():
        raise ErroApi("Loja não encontrada.", status=404)
    antiga = db.execute("SELECT * FROM avaliacao WHERE id_cliente = ? AND id_loja = ?", (usuario["id_usuario"], id_loja)).fetchone()
    ex = gamificacao.ler_extras(d, _aj, antiga)
    try:
        gamificacao.iniciar_escrita(db)
        foto = ex["foto_nova"] if ex["foto_nova"] else (antiga["foto"] if antiga else None)
        db.execute(
            """INSERT INTO avaliacao (id_cliente, id_loja, nota, comentario, crit_atendimento, crit_qualidade, crit_preco, crit_ambiente, dica, consumiu, foto)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT (id_cliente, id_loja)
               DO UPDATE SET nota = excluded.nota, comentario = excluded.comentario, crit_atendimento = excluded.crit_atendimento,
                 crit_qualidade = excluded.crit_qualidade, crit_preco = excluded.crit_preco, crit_ambiente = excluded.crit_ambiente,
                 dica = excluded.dica, consumiu = excluded.consumiu, foto = excluded.foto, data_criacao = CURRENT_DATE""",
            (usuario["id_usuario"], id_loja, nota, ex["comentario"], ex["criterios"].get("atendimento"), ex["criterios"].get("qualidade"),
             ex["criterios"].get("preco"), ex["criterios"].get("ambiente"), ex["dica"], ex["consumiu"], foto),
        )
        linha = db.execute("SELECT * FROM avaliacao WHERE id_cliente = ? AND id_loja = ?", (usuario["id_usuario"], id_loja)).fetchone()
        ganho = gamificacao.conceder_pontos_avaliacao(db, usuario, id_loja, linha["id_avaliacao"], linha, linha["pontos_base_concedidos"])
        dono = db.execute("SELECT id_logista, nome_fantasia FROM loja WHERE id_loja = ?", (id_loja,)).fetchone()
        anonimo = not conta.preferencias_de(usuario)["privacidade"]["nome_nas_avaliacoes"]
        quem = "Um cliente" if anonimo else usuario["nome"].split()[0]
        conta.notificar(dono["id_logista"], "avaliacoes", "Nova avaliação: %d de 5" % nota, "%s avaliou %s." % (quem, dono["nome_fantasia"]), "minha_loja.html")
        conta.registrar_atividade(usuario["id_usuario"], "Avaliou uma loja", "%s: %d de 5" % (dono["nome_fantasia"], nota))
        db.commit()
    except BaseException:
        db.rollback()
        raise
    return jsonify({"ok": True, "ganho": ganho}), 201


@app.post("/api/lojas/<int:id_loja>/pedidos")
@exigir("CLIENTE")
def reservar(usuario, id_loja):
    d = dados_json()
    db = banco.conexao()
    item = db.execute(
        "SELECT * FROM item_vitrine WHERE id_item = ? AND id_loja = ?", (d.get("id_item"), id_loja)
    ).fetchone()
    if item is None:
        raise ErroApi("Item não encontrado nessa loja.", status=404)
    db.execute(
        "INSERT INTO pedido (id_cliente, id_loja, item, valor) VALUES (?, ?, ?, ?)",
        (usuario["id_usuario"], id_loja, item["nome"], item["valor"]),
    )
    dono = db.execute("SELECT id_logista, nome_fantasia FROM loja WHERE id_loja = ?", (id_loja,)).fetchone()
    conta.notificar(dono["id_logista"], "pedidos", "Novo pedido: %s" % item["nome"], "%s fez um pedido de R$ %.2f." % (usuario["nome"].split()[0], item["valor"]), "minha_loja.html")
    conta.notificar(usuario["id_usuario"], "pedidos", "Pedido registrado", "%s em %s." % (item["nome"], dono["nome_fantasia"]), "explorar.html")
    conta.registrar_atividade(usuario["id_usuario"], "Fez um pedido", "%s em %s" % (item["nome"], dono["nome_fantasia"]))
    db.commit()
    return jsonify({"ok": True}), 201


@app.get("/api/meus-pedidos")
@exigir("CLIENTE")
def meus_pedidos(usuario):
    linhas = banco.conexao().execute(
        """SELECT p.*, l.nome_fantasia FROM pedido p JOIN loja l ON l.id_loja = p.id_loja
           WHERE p.id_cliente = ? ORDER BY p.id_pedido DESC""",
        (usuario["id_usuario"],),
    ).fetchall()
    return jsonify(
        {"pedidos": [{"item": p["item"], "valor": p["valor"], "loja": p["nome_fantasia"], "data": p["criado_em"][:10]} for p in linhas]}
    )


# ---------------------------------------------------------------- comerciante (LOGISTA)
def minha_loja_linha(usuario):
    linha = banco.conexao().execute("SELECT * FROM loja WHERE id_logista = ?", (usuario["id_usuario"],)).fetchone()
    if linha is None:
        raise ErroApi("Loja não encontrada.", status=404)
    return linha


@app.get("/api/minha-loja")
@exigir("LOGISTA")
def minha_loja(usuario):
    linha = minha_loja_linha(usuario)
    saida = loja_para_dict(linha)
    log = banco.conexao().execute("SELECT * FROM logista WHERE id_usuario = ?", (usuario["id_usuario"],)).fetchone()
    saida["cnpj"] = log["cnpj"]
    saida["razao_social"] = log["razao_social"]
    saida["responsavel"] = usuario["nome"]
    saida["eventos"] = [
        evento_para_dict(e)
        for e in banco.conexao().execute("SELECT * FROM evento WHERE id_loja = ? ORDER BY id_evento DESC", (linha["id_loja"],))
    ]
    return jsonify({"loja": saida})


@app.put("/api/minha-loja")
@exigir("LOGISTA")
def atualizar_loja(usuario):
    linha = minha_loja_linha(usuario)
    d = dados_json()
    erros = {}
    cnpj_novo, razao = validar_cnpj_opcional(d, erros)
    loja = validar_loja(d, erros)
    if erros:
        raise ErroApi("Corrija os campos destacados.", erros)
    # foto/logo não enviadas continuam como estavam
    if "logo" not in d:
        loja["logo"] = linha["logo"]
    if "foto" not in d:
        loja["foto"] = linha["foto"]
    db = banco.conexao()
    try:
        db.execute(
            """UPDATE loja SET nome_fantasia=:nome_fantasia, segmento=:segmento, descricao=:descricao, cep=:cep,
                      rua=:rua, numero=:numero, bairro=:bairro, cidade=:cidade, estado=:estado,
                      latitude=:latitude, longitude=:longitude, horarios=:horarios, telefone=:telefone,
                      whatsapp=:whatsapp, instagram=:instagram, site=:site, logo=:logo, foto=:foto
               WHERE id_loja=:id""",
            dict(loja, id=linha["id_loja"]),
        )
        db.execute("UPDATE logista SET cnpj = ?, razao_social = ? WHERE id_usuario = ?", (cnpj_novo, razao, usuario["id_usuario"]))
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        raise ErroApi("Corrija os campos destacados.", {"cnpj": "Este CNPJ já está cadastrado."})
    return jsonify({"ok": True})


@app.post("/api/minha-loja/vitrine")
@exigir("LOGISTA")
def vitrine_adicionar(usuario):
    linha = minha_loja_linha(usuario)
    d = dados_json()
    nome = texto(d, "nome", 100)
    try:
        valor = float(d.get("valor"))
        assert valor >= 0
    except (TypeError, ValueError, AssertionError):
        raise ErroApi("Valor inválido.", {"valor": "Informe um valor válido."})
    if not nome:
        raise ErroApi("Informe o nome do item.", {"nome": "Informe o nome do item."})
    db = banco.conexao()
    cur = db.execute(
        "INSERT INTO item_vitrine (id_loja, nome, valor, foto) VALUES (?, ?, ?, ?)",
        (linha["id_loja"], nome, valor, imagem_valida(d.get("foto"))),
    )
    db.commit()
    return jsonify({"id": cur.lastrowid}), 201


@app.delete("/api/minha-loja/vitrine/<int:id_item>")
@exigir("LOGISTA")
def vitrine_remover(usuario, id_item):
    linha = minha_loja_linha(usuario)
    db = banco.conexao()
    db.execute("DELETE FROM item_vitrine WHERE id_item = ? AND id_loja = ?", (id_item, linha["id_loja"]))
    db.commit()
    return jsonify({"ok": True})


@app.post("/api/minha-loja/eventos")
@exigir("LOGISTA")
def evento_adicionar(usuario):
    linha = minha_loja_linha(usuario)
    d = dados_json()
    nome = texto(d, "nome", 100)
    dia = texto(d, "dia", 20)
    horario = texto(d, "horario", 5)
    erros = {}
    if not nome:
        erros["nome"] = "Informe o nome do evento."
    if dia not in DIAS_EVENTO:
        erros["dia"] = "Escolha o dia."
    if not re.match(r"^\d{2}:\d{2}$", horario):
        erros["horario"] = "Informe o horário."
    lat = lng = None
    if d.get("latitude") not in (None, "") or d.get("longitude") not in (None, ""):
        try:
            lat, lng = float(d.get("latitude")), float(d.get("longitude"))
            assert -90 <= lat <= 90 and -180 <= lng <= 180
        except (TypeError, ValueError, AssertionError):
            erros["latitude"] = "Latitude/longitude inválidas."
    if erros:
        raise ErroApi("Corrija os campos destacados.", erros)
    db = banco.conexao()
    cur = db.execute(
        "INSERT INTO evento (id_loja, nome, dia_semana, horario, descricao, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (linha["id_loja"], nome, dia, horario, texto(d, "descricao", 300), lat, lng),
    )
    # avisa quem já avaliou ou pediu nesta loja
    interessados = db.execute(
        "SELECT id_cliente FROM avaliacao WHERE id_loja = ? UNION SELECT id_cliente FROM pedido WHERE id_loja = ?",
        (linha["id_loja"], linha["id_loja"]),
    ).fetchall()
    for i in interessados:
        conta.notificar(i["id_cliente"], "eventos", "Novo evento: %s" % nome, "%s anunciou um evento na %s, às %s." % (linha["nome_fantasia"], dia, horario), "explorar.html")
    db.commit()
    return jsonify({"id": cur.lastrowid}), 201


@app.delete("/api/minha-loja/eventos/<int:id_evento>")
@exigir("LOGISTA")
def evento_remover(usuario, id_evento):
    linha = minha_loja_linha(usuario)
    db = banco.conexao()
    db.execute("DELETE FROM evento WHERE id_evento = ? AND id_loja = ?", (id_evento, linha["id_loja"]))
    db.commit()
    return jsonify({"ok": True})


@app.get("/api/minha-loja/avaliacoes")
@exigir("LOGISTA")
def minhas_avaliacoes(usuario):
    linha = minha_loja_linha(usuario)
    return avaliacoes_da_loja(linha["id_loja"])


@app.get("/api/minha-loja/estatisticas")
@exigir("LOGISTA")
def estatisticas(usuario):
    linha = minha_loja_linha(usuario)
    db = banco.conexao()
    id_loja = linha["id_loja"]
    ped = db.execute("SELECT COUNT(*) AS n, COALESCE(SUM(valor), 0) AS total FROM pedido WHERE id_loja = ?", (id_loja,)).fetchone()
    nota = db.execute("SELECT AVG(nota) AS media, COUNT(*) AS n FROM avaliacao WHERE id_loja = ?", (id_loja,)).fetchone()
    por_nota = {str(n): 0 for n in range(1, 6)}
    for r in db.execute("SELECT nota, COUNT(*) AS n FROM avaliacao WHERE id_loja = ? GROUP BY nota", (id_loja,)):
        por_nota[str(r["nota"])] = r["n"]
    recentes = db.execute(
        """SELECT p.*, u.nome FROM pedido p JOIN usuario u ON u.id_usuario = p.id_cliente
           WHERE p.id_loja = ? ORDER BY p.id_pedido DESC LIMIT 10""",
        (id_loja,),
    ).fetchall()
    return jsonify(
        {
            "total_vendido": ped["total"],
            "pedidos": ped["n"],
            "ticket_medio": (ped["total"] / ped["n"]) if ped["n"] else 0,
            "nota_media": round(nota["media"], 1) if nota["media"] else None,
            "total_avaliacoes": nota["n"],
            "avaliacoes_por_nota": por_nota,
            "itens": db.execute("SELECT COUNT(*) FROM item_vitrine WHERE id_loja = ?", (id_loja,)).fetchone()[0],
            "eventos": db.execute("SELECT COUNT(*) FROM evento WHERE id_loja = ?", (id_loja,)).fetchone()[0],
            "ultimos_pedidos": [
                {"item": p["item"], "valor": p["valor"], "cliente": p["nome"].split()[0], "data": p["criado_em"][:10]}
                for p in recentes
            ],
        }
    )


class _Ajudantes:
    pass


_aj = _Ajudantes()
for _nome, _valor in dict(ErroApi=ErroApi, dados_json=dados_json, texto=texto, so_digitos=so_digitos, exigir=exigir,
                          imagem_valida=imagem_valida, validar_senha_nova=validar_senha_nova,
                          usuario_logado=usuario_logado).items():
    setattr(_aj, _nome, _valor)
conta.registrar_rotas(app, _aj)
agenda.registrar_rotas(app)
gamificacao.registrar_rotas(app, _aj)
lgpd.registrar_rotas(app, _aj)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=os.environ.get("FLASK_DEBUG") == "1")
