"""Nordestinando - conta do usuário: perfil, senha, sessões, notificações e recuperação de senha.

Este módulo não importa o app.py (evita import circular). O app.py chama
`conta.registrar_rotas(app, ajudantes)` passando as funções que as rotas precisam.
"""
import hashlib
import json
import os
import re
import secrets
import smtplib
import sqlite3
import time
from email.message import EmailMessage

from flask import jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

import banco

CATEGORIAS = ("avaliacoes", "pedidos", "eventos", "seguranca")
ROTULOS = {
    "avaliacoes": "Avaliações",
    "pedidos": "Pedidos",
    "eventos": "Eventos",
    "seguranca": "Segurança",
}
PADRAO = {
    "tema": "auto",
    "notif": {"avaliacoes": True, "pedidos": True, "eventos": True},
    "privacidade": {"nome_nas_avaliacoes": True},
}

LIMITE_LOGIN = (5, 10 * 60)  # 5 erros a cada 10 minutos
LIMITE_ESQUECI = (5, 60 * 60)  # 5 pedidos por hora
VALIDADE_LINK = 60 * 60  # link de senha vale 1 hora
MAX_SESSAO_DIAS = 30


# ---------------------------------------------------------------- utilidades
def _hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def preferencias_de(linha):
    """Preferências do usuário já completas (o que faltar vem do padrão)."""
    try:
        salvas = json.loads(linha["preferencias"] or "{}")
    except (ValueError, TypeError):
        salvas = {}
    saida = json.loads(json.dumps(PADRAO))
    if salvas.get("tema") in ("auto", "claro", "escuro"):
        saida["tema"] = salvas["tema"]
    for chave in saida["notif"]:
        if isinstance(salvas.get("notif", {}).get(chave), bool):
            saida["notif"][chave] = salvas["notif"][chave]
    if isinstance(salvas.get("privacidade", {}).get("nome_nas_avaliacoes"), bool):
        saida["privacidade"]["nome_nas_avaliacoes"] = salvas["privacidade"]["nome_nas_avaliacoes"]
    return saida


def registrar_atividade(id_usuario, acao, detalhe=""):
    banco.conexao().execute(
        "INSERT INTO atividade (id_usuario, acao, detalhe) VALUES (?, ?, ?)", (id_usuario, acao, detalhe[:200])
    )


def notificar(id_usuario, categoria, titulo, mensagem, link=None):
    """Cria uma notificação real, respeitando as preferências da pessoa (segurança sempre chega)."""
    db = banco.conexao()
    u = db.execute("SELECT preferencias FROM usuario WHERE id_usuario = ?", (id_usuario,)).fetchone()
    if u is None:
        return
    if categoria != "seguranca" and not preferencias_de(u)["notif"].get(categoria, True):
        return
    db.execute(
        "INSERT INTO notificacao (id_usuario, categoria, titulo, mensagem, link) VALUES (?, ?, ?, ?, ?)",
        (id_usuario, categoria, titulo[:120], mensagem[:300], link),
    )


def _descrever_agente(texto):
    texto = texto or ""
    navegador = "Navegador"
    for marca, nome in (("Edg/", "Edge"), ("OPR/", "Opera"), ("Firefox/", "Firefox"), ("Chrome/", "Chrome"), ("Safari/", "Safari")):
        if marca in texto:
            navegador = nome
            break
    sistema = "dispositivo desconhecido"
    for marca, nome in (("Android", "Android"), ("iPhone", "iPhone"), ("iPad", "iPad"), ("Windows", "Windows"), ("Mac OS", "macOS"), ("Linux", "Linux")):
        if marca in texto:
            sistema = nome
            break
    return "%s em %s" % (navegador, sistema)


# ---------------------------------------------------------------- sessões
def iniciar_sessao(id_usuario):
    """Cria uma sessão nova (troca a anterior do cookie) e devolve nada; o cookie guarda o token."""
    token = secrets.token_urlsafe(32)
    banco.conexao().execute(
        "INSERT INTO sessao (id_usuario, token_hash, ip, agente) VALUES (?, ?, ?, ?)",
        (id_usuario, _hash(token), request.remote_addr, _descrever_agente(request.headers.get("User-Agent"))),
    )
    session.clear()
    session["token"] = token
    session.permanent = True


def encerrar_sessao_atual():
    token = session.get("token")
    if token:
        banco.conexao().execute("DELETE FROM sessao WHERE token_hash = ?", (_hash(token),))
        banco.conexao().commit()
    session.clear()


def id_usuario_da_sessao():
    """Id do usuário da sessão do cookie, só se a sessão ainda existir no banco e não tiver vencido."""
    token = session.get("token")
    if not token:
        return None
    db = banco.conexao()
    linha = db.execute(
        "SELECT id_sessao, id_usuario, criado_em, ultimo_uso FROM sessao WHERE token_hash = ?", (_hash(token),)
    ).fetchone()
    if linha is None:
        session.clear()
        return None
    idade = db.execute("SELECT julianday('now') - julianday(?) AS d", (linha["criado_em"],)).fetchone()["d"]
    if idade > MAX_SESSAO_DIAS:
        db.execute("DELETE FROM sessao WHERE id_sessao = ?", (linha["id_sessao"],))
        db.commit()
        session.clear()
        return None
    # atualiza "último uso" no máximo a cada 5 minutos
    parado = db.execute("SELECT (julianday('now') - julianday(?)) * 1440 AS m", (linha["ultimo_uso"],)).fetchone()["m"]
    if parado > 5:
        db.execute("UPDATE sessao SET ultimo_uso = CURRENT_TIMESTAMP WHERE id_sessao = ?", (linha["id_sessao"],))
        db.commit()
    return linha["id_usuario"]


def _id_sessao_atual():
    token = session.get("token")
    if not token:
        return None
    r = banco.conexao().execute("SELECT id_sessao FROM sessao WHERE token_hash = ?", (_hash(token),)).fetchone()
    return r["id_sessao"] if r else None


# ---------------------------------------------------------------- limite de tentativas
def tentativas_recentes(tipo, chave, janela):
    db = banco.conexao()
    agora = time.time()
    db.execute("DELETE FROM tentativa WHERE criada_em < ?", (agora - 24 * 3600,))
    return db.execute(
        "SELECT COUNT(*) AS n FROM tentativa WHERE tipo = ? AND chave = ? AND criada_em > ?", (tipo, chave, agora - janela)
    ).fetchone()["n"]


def registrar_tentativa(tipo, chave):
    banco.conexao().execute("INSERT INTO tentativa (tipo, chave, criada_em) VALUES (?, ?, ?)", (tipo, chave, time.time()))
    banco.conexao().commit()


def limpar_tentativas(tipo, chave):
    banco.conexao().execute("DELETE FROM tentativa WHERE tipo = ? AND chave = ?", (tipo, chave))
    banco.conexao().commit()


# ---------------------------------------------------------------- e-mail
def enviar_email(destino, assunto, corpo):
    """Envia por SMTP se estiver configurado no .env. Devolve 'email' ou 'console'."""
    host = os.environ.get("SMTP_HOST")
    if not host:
        print("\n[e-mail não configurado] Para: %s\nAssunto: %s\n%s\n" % (destino, assunto, corpo), flush=True)
        return "console"
    msg = EmailMessage()
    msg["From"] = os.environ.get("SMTP_FROM") or os.environ.get("SMTP_USER") or "nao-responda@localhost"
    msg["To"] = destino
    msg["Subject"] = assunto
    msg.set_content(corpo)
    porta = int(os.environ.get("SMTP_PORT", "587"))
    usuario, senha = os.environ.get("SMTP_USER"), os.environ.get("SMTP_PASSWORD")
    if porta == 465:
        servidor = smtplib.SMTP_SSL(host, porta, timeout=15)
    else:
        servidor = smtplib.SMTP(host, porta, timeout=15)
        servidor.starttls()
    with servidor:
        if usuario:
            servidor.login(usuario, senha or "")
        servidor.send_message(msg)
    return "email"


# ---------------------------------------------------------------- rotas
def registrar_rotas(app, h):
    """h: objeto com ErroApi, dados_json, texto, so_digitos, exigir, imagem_valida, validar_senha_nova."""
    ErroApi, dados_json, texto, exigir = h.ErroApi, h.dados_json, h.texto, h.exigir

    def conta_dict(u):
        db = banco.conexao()
        saida = {
            "id": u["id_usuario"],
            "nome": u["nome"],
            "email": u["email"],
            "telefone": u["telefone"] or "",
            "perfil": u["perfil"],
            "avatar": u["avatar"],
            "criado_em": u["criado_em"],
            "preferencias": preferencias_de(u),
        }
        if u["perfil"] == "CLIENTE":
            saida["resumo"] = {
                "avaliacoes": db.execute("SELECT COUNT(*) FROM avaliacao WHERE id_cliente = ?", (u["id_usuario"],)).fetchone()[0],
                "pedidos": db.execute("SELECT COUNT(*) FROM pedido WHERE id_cliente = ?", (u["id_usuario"],)).fetchone()[0],
            }
        else:
            loja = db.execute("SELECT id_loja, nome_fantasia FROM loja WHERE id_logista = ?", (u["id_usuario"],)).fetchone()
            log = db.execute("SELECT cnpj, razao_social FROM logista WHERE id_usuario = ?", (u["id_usuario"],)).fetchone()
            saida["resumo"] = {
                "loja": loja["nome_fantasia"] if loja else None,
                "cnpj": log["cnpj"] if log else None,
                "razao_social": log["razao_social"] if log else None,
            }
        return saida

    # ---------- perfil
    @app.get("/api/conta")
    @exigir()
    def ver_conta(u):
        return jsonify({"conta": conta_dict(u)})

    @app.patch("/api/conta")
    @exigir()
    def editar_conta(u):
        d = dados_json()
        erros = {}
        nome = texto(d, "nome", 100)
        email = texto(d, "email", 150).lower()
        telefone = h.so_digitos(texto(d, "telefone", 20))
        if len(nome) < 3:
            erros["nome"] = "Informe o nome completo."
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            erros["email"] = "E-mail inválido."
        if len(telefone) not in (10, 11):
            erros["telefone"] = "Telefone com DDD, 10 ou 11 dígitos."
        mudou_email = email != u["email"]
        if mudou_email and not erros.get("email"):
            if not check_password_hash(u["senha_hash"], str(d.get("senha_atual") or "")):
                erros["senha_atual"] = "Para trocar o e-mail, digite sua senha atual."
        if erros:
            raise ErroApi("Corrija os campos destacados.", erros)
        db = banco.conexao()
        try:
            db.execute(
                "UPDATE usuario SET nome = ?, email = ?, telefone = ? WHERE id_usuario = ?",
                (nome, email, telefone, u["id_usuario"]),
            )
            registrar_atividade(u["id_usuario"], "Dados atualizados", "E-mail alterado" if mudou_email else "")
            if mudou_email:
                notificar(u["id_usuario"], "seguranca", "E-mail alterado", "O e-mail da sua conta foi alterado para %s." % email)
            db.commit()
        except sqlite3.IntegrityError:
            db.rollback()
            raise ErroApi("Corrija os campos destacados.", {"email": "Este e-mail já está em uso."})
        return jsonify({"conta": conta_dict(h.usuario_logado())})

    @app.post("/api/conta/foto")
    @exigir()
    def trocar_foto(u):
        d = dados_json()
        imagem = h.imagem_valida(d.get("imagem"))
        db = banco.conexao()
        db.execute("UPDATE usuario SET avatar = ? WHERE id_usuario = ?", (imagem or None, u["id_usuario"]))
        registrar_atividade(u["id_usuario"], "Foto de perfil " + ("alterada" if imagem else "removida"))
        db.commit()
        return jsonify({"avatar": imagem or None})

    # ---------- senha
    @app.post("/api/conta/senha")
    @exigir()
    def trocar_senha(u):
        d = dados_json()
        erros = {}
        if not check_password_hash(u["senha_hash"], str(d.get("senha_atual") or "")):
            erros["senha_atual"] = "Senha atual incorreta."
        nova = str(d.get("senha") or "")
        h.validar_senha_nova(nova, str(d.get("confirmar_senha") or ""), erros)
        if not erros and check_password_hash(u["senha_hash"], nova):
            erros["senha"] = "A nova senha precisa ser diferente da atual."
        if erros:
            raise ErroApi("Corrija os campos destacados.", erros)
        db = banco.conexao()
        db.execute("UPDATE usuario SET senha_hash = ? WHERE id_usuario = ?", (generate_password_hash(nova), u["id_usuario"]))
        # sai de todos os outros aparelhos
        db.execute("DELETE FROM sessao WHERE id_usuario = ? AND id_sessao != ?", (u["id_usuario"], _id_sessao_atual() or 0))
        registrar_atividade(u["id_usuario"], "Senha alterada")
        notificar(u["id_usuario"], "seguranca", "Senha alterada", "Sua senha foi alterada. Os outros aparelhos foram desconectados.")
        db.commit()
        return jsonify({"ok": True})

    # ---------- preferências
    @app.get("/api/conta/preferencias")
    @exigir()
    def ver_preferencias(u):
        return jsonify({"preferencias": preferencias_de(u)})

    @app.put("/api/conta/preferencias")
    @exigir()
    def salvar_preferencias(u):
        d = dados_json()
        atual = preferencias_de(u)
        if "tema" in d:
            if d["tema"] not in ("auto", "claro", "escuro"):
                raise ErroApi("Tema inválido.", {"tema": "Escolha automático, claro ou escuro."})
            atual["tema"] = d["tema"]
        for chave, valor in (d.get("notif") or {}).items():
            if chave in atual["notif"]:
                if not isinstance(valor, bool):
                    raise ErroApi("Valor inválido.")
                atual["notif"][chave] = valor
        valor = (d.get("privacidade") or {}).get("nome_nas_avaliacoes")
        if valor is not None:
            if not isinstance(valor, bool):
                raise ErroApi("Valor inválido.")
            atual["privacidade"]["nome_nas_avaliacoes"] = valor
        db = banco.conexao()
        db.execute("UPDATE usuario SET preferencias = ? WHERE id_usuario = ?", (json.dumps(atual), u["id_usuario"]))
        db.commit()
        return jsonify({"preferencias": atual})

    # ---------- sessões e histórico
    @app.get("/api/conta/sessoes")
    @exigir()
    def listar_sessoes(u):
        atual = _id_sessao_atual()
        linhas = banco.conexao().execute(
            "SELECT * FROM sessao WHERE id_usuario = ? ORDER BY ultimo_uso DESC", (u["id_usuario"],)
        ).fetchall()
        return jsonify(
            {
                "sessoes": [
                    {
                        "id": s["id_sessao"],
                        "agente": s["agente"],
                        "ip": s["ip"],
                        "criado_em": s["criado_em"],
                        "ultimo_uso": s["ultimo_uso"],
                        "atual": s["id_sessao"] == atual,
                    }
                    for s in linhas
                ]
            }
        )

    @app.delete("/api/conta/sessoes/<int:id_sessao>")
    @exigir()
    def encerrar_sessao(u, id_sessao):
        if id_sessao == _id_sessao_atual():
            raise ErroApi("Esta é a sessão atual. Use “Sair da conta”.")
        db = banco.conexao()
        cur = db.execute("DELETE FROM sessao WHERE id_sessao = ? AND id_usuario = ?", (id_sessao, u["id_usuario"]))
        if cur.rowcount == 0:
            raise ErroApi("Sessão não encontrada.", status=404)
        registrar_atividade(u["id_usuario"], "Sessão encerrada", "Um aparelho foi desconectado")
        db.commit()
        return jsonify({"ok": True})

    @app.post("/api/conta/sessoes/encerrar-outras")
    @exigir()
    def encerrar_outras(u):
        db = banco.conexao()
        cur = db.execute("DELETE FROM sessao WHERE id_usuario = ? AND id_sessao != ?", (u["id_usuario"], _id_sessao_atual() or 0))
        registrar_atividade(u["id_usuario"], "Outras sessões encerradas", "%d aparelho(s)" % cur.rowcount)
        db.commit()
        return jsonify({"encerradas": cur.rowcount})

    @app.get("/api/conta/atividades")
    @exigir()
    def atividades(u):
        linhas = banco.conexao().execute(
            "SELECT acao, detalhe, criada_em FROM atividade WHERE id_usuario = ? ORDER BY id_atividade DESC LIMIT 30",
            (u["id_usuario"],),
        ).fetchall()
        return jsonify({"atividades": [dict(a) for a in linhas]})

    @app.delete("/api/conta")
    @exigir()
    def excluir_conta(u):
        d = dados_json()
        erros = {}
        if not check_password_hash(u["senha_hash"], str(d.get("senha") or "")):
            erros["senha"] = "Senha incorreta."
        if str(d.get("confirmacao") or "").strip().upper() != "EXCLUIR":
            erros["confirmacao"] = "Digite EXCLUIR para confirmar."
        if erros:
            raise ErroApi("Não foi possível excluir a conta.", erros)
        db = banco.conexao()
        # as chaves estrangeiras em cascata apagam loja, pedidos, avaliações, sessões e notificações
        db.execute("DELETE FROM usuario WHERE id_usuario = ?", (u["id_usuario"],))
        db.commit()
        session.clear()
        return jsonify({"ok": True})

    # ---------- notificações
    def notif_dict(n):
        return {
            "id": n["id_notificacao"],
            "categoria": n["categoria"],
            "rotulo": ROTULOS[n["categoria"]],
            "titulo": n["titulo"],
            "mensagem": n["mensagem"],
            "link": n["link"],
            "lida": bool(n["lida"]),
            "criada_em": n["criada_em"],
        }

    @app.get("/api/notificacoes")
    @exigir()
    def listar_notificacoes(u):
        db = banco.conexao()
        filtro = "AND lida = 0" if request.args.get("so_nao_lidas") == "1" else ""
        linhas = db.execute(
            "SELECT * FROM notificacao WHERE id_usuario = ? %s ORDER BY id_notificacao DESC LIMIT 100" % filtro,
            (u["id_usuario"],),
        ).fetchall()
        nao_lidas = db.execute("SELECT COUNT(*) FROM notificacao WHERE id_usuario = ? AND lida = 0", (u["id_usuario"],)).fetchone()[0]
        return jsonify({"notificacoes": [notif_dict(n) for n in linhas], "nao_lidas": nao_lidas})

    @app.get("/api/notificacoes/contagem")
    @exigir()
    def contar_notificacoes(u):
        n = banco.conexao().execute("SELECT COUNT(*) FROM notificacao WHERE id_usuario = ? AND lida = 0", (u["id_usuario"],)).fetchone()[0]
        return jsonify({"nao_lidas": n})

    @app.post("/api/notificacoes/<int:id_n>/lida")
    @exigir()
    def marcar_lida(u, id_n):
        db = banco.conexao()
        cur = db.execute("UPDATE notificacao SET lida = 1 WHERE id_notificacao = ? AND id_usuario = ?", (id_n, u["id_usuario"]))
        if cur.rowcount == 0:
            raise ErroApi("Notificação não encontrada.", status=404)
        db.commit()
        return jsonify({"ok": True})

    @app.post("/api/notificacoes/lidas")
    @exigir()
    def marcar_todas(u):
        db = banco.conexao()
        cur = db.execute("UPDATE notificacao SET lida = 1 WHERE id_usuario = ? AND lida = 0", (u["id_usuario"],))
        db.commit()
        return jsonify({"marcadas": cur.rowcount})

    @app.delete("/api/notificacoes/<int:id_n>")
    @exigir()
    def excluir_notificacao(u, id_n):
        db = banco.conexao()
        cur = db.execute("DELETE FROM notificacao WHERE id_notificacao = ? AND id_usuario = ?", (id_n, u["id_usuario"]))
        if cur.rowcount == 0:
            raise ErroApi("Notificação não encontrada.", status=404)
        db.commit()
        return jsonify({"ok": True})

    @app.delete("/api/notificacoes")
    @exigir()
    def limpar_lidas(u):
        db = banco.conexao()
        cur = db.execute("DELETE FROM notificacao WHERE id_usuario = ? AND lida = 1", (u["id_usuario"],))
        db.commit()
        return jsonify({"excluidas": cur.rowcount})

    # ---------- recuperação de senha
    @app.post("/api/senha/esqueci")
    def esqueci_senha():
        d = dados_json()
        email = texto(d, "email", 150).lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            raise ErroApi("Digite um e-mail válido.", {"email": "E-mail inválido."})
        chave = request.remote_addr or "?"
        if tentativas_recentes("esqueci", chave, LIMITE_ESQUECI[1]) >= LIMITE_ESQUECI[0]:
            raise ErroApi("Muitos pedidos. Tente de novo em alguns minutos.", status=429)
        registrar_tentativa("esqueci", chave)
        entrega = "email" if os.environ.get("SMTP_HOST") else "console"
        db = banco.conexao()
        u = db.execute("SELECT * FROM usuario WHERE email = ?", (email,)).fetchone()
        if u is not None:
            token = secrets.token_urlsafe(32)
            db.execute(
                "INSERT INTO redefinicao_senha (token_hash, id_usuario, expira_em) VALUES (?, ?, ?)",
                (_hash(token), u["id_usuario"], time.time() + VALIDADE_LINK),
            )
            registrar_atividade(u["id_usuario"], "Recuperação de senha solicitada")
            db.commit()
            base = (os.environ.get("APP_URL") or request.host_url).rstrip("/")
            link = "%s/html/redefinir_senha.html?token=%s" % (base, token)
            try:
                entrega = enviar_email(
                    email,
                    "Nordestinando - redefinir sua senha",
                    "Olá, %s!\n\nPara criar uma nova senha, abra o link (vale por 1 hora):\n%s\n\n"
                    "Se não foi você, ignore este e-mail." % (u["nome"].split()[0], link),
                )
            except (OSError, smtplib.SMTPException) as erro:
                print("[erro ao enviar e-mail]", erro, flush=True)
                # não revela nada para quem pediu; o administrador vê no terminal
        # a resposta é a mesma exista ou não a conta (não revela quem tem cadastro)
        return jsonify({"ok": True, "entrega": entrega})

    @app.post("/api/senha/redefinir")
    def redefinir_senha():
        d = dados_json()
        erros = {}
        h.validar_senha_nova(str(d.get("senha") or ""), str(d.get("confirmar_senha") or ""), erros)
        if erros:
            raise ErroApi("Corrija os campos destacados.", erros)
        db = banco.conexao()
        r = db.execute(
            "SELECT * FROM redefinicao_senha WHERE token_hash = ?", (_hash(str(d.get("token") or "")),)
        ).fetchone()
        if r is None or r["usada"] or r["expira_em"] < time.time():
            raise ErroApi("Este link não vale mais. Peça um novo em “Esqueci minha senha”.", status=400)
        db.execute("UPDATE usuario SET senha_hash = ? WHERE id_usuario = ?", (generate_password_hash(str(d["senha"])), r["id_usuario"]))
        db.execute("UPDATE redefinicao_senha SET usada = 1 WHERE id_usuario = ?", (r["id_usuario"],))
        db.execute("DELETE FROM sessao WHERE id_usuario = ?", (r["id_usuario"],))
        registrar_atividade(r["id_usuario"], "Senha redefinida pelo link")
        notificar(r["id_usuario"], "seguranca", "Senha redefinida", "Sua senha foi redefinida e todos os aparelhos foram desconectados.")
        db.commit()
        return jsonify({"ok": True})
