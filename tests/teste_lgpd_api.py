"""Testes de LGPD: aceite obrigatório e versionado, exportação, exclusão completa, retenção. Banco temporário."""
import os, sys, tempfile, json, time
os.environ["DB_PATH"] = tempfile.mkdtemp() + "/t.db"; os.environ["SECRET_KEY"] = "x"
os.environ.pop("LGPD_CONTATO_EMAIL", None)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "python"))
import app as A, banco, lgpd  # noqa: E402
ok = fail = 0
def t(nome, cond, extra=""):
    global ok, fail
    if cond: ok += 1
    else: fail += 1; print("FALHOU:", nome, extra)
J = lambda r: r.get_json()
cli = A.app.test_client
cad = dict(nome="Maria Silva", email="maria@x.com", telefone="81999998888", senha="senha1234", confirmar_senha="senha1234")
loja = dict(nome_fantasia="Loja do João", segmento="Outros", descricao="Descrição da loja", cep="55012000", rua="Rua A", numero="1", bairro="Centro", cidade="Caruaru", estado="PE", latitude=-8.28, longitude=-35.97, telefone_comercial="81988887777",
            horarios={k: {"fechado": False, "abre": "08:00", "fecha": "18:00"} for k in A.DIAS})
# aceite obrigatório
c = cli()
r = c.post("/api/cadastro/usuario", json=cad); t("sem aceite recusa", r.status_code == 400 and "aceite" in J(r)["campos"])
r = c.post("/api/cadastro/usuario", json=dict(cad, aceite="sim")); t("aceite precisa ser true", r.status_code == 400)
t("sem aceite comerciante", cli().post("/api/cadastro/comerciante", json=dict(cad, email="j@x.com", **loja)).status_code == 400)
r = c.post("/api/cadastro/usuario", json=dict(cad, aceite=True)); t("com aceite cria", r.status_code == 201)
lj = cli(); t("comerciante com aceite", lj.post("/api/cadastro/comerciante", json=dict(cad, email="j@x.com", aceite=True, **loja)).status_code == 201)
ac = J(c.get("/api/lgpd/aceite")); t("aceite registrado", ac["aceitou"] == ac["atual"] and not ac["precisa_reaceitar"])
with A.app.app_context():
    n = banco.conexao().execute("SELECT COUNT(*) FROM consentimento").fetchone()[0]
t("2 documentos por conta", n == 4)
# nova versão exige novo aceite
with A.app.app_context():
    con = banco.conexao(); con.execute("UPDATE consentimento SET versao = '2000-01-01'"); con.commit()
t("versão antiga pede reaceite", J(c.get("/api/lgpd/aceite"))["precisa_reaceitar"])
t("reaceite exige marcar", c.post("/api/lgpd/aceite", json={}).status_code == 400)
t("reaceita", c.post("/api/lgpd/aceite", json={"aceite": True}).status_code == 200 and not J(c.get("/api/lgpd/aceite"))["precisa_reaceitar"])
t("aceite exige login", cli().get("/api/lgpd/aceite").status_code == 401)
# info pública sem inventar contato
i = J(cli().get("/api/lgpd/info")); t("info sem contato inventado", i["contato"] is None and i["controlador"])
os.environ["LGPD_CONTATO_EMAIL"] = "privacidade@exemplo.com"
t("contato vem do ambiente", J(cli().get("/api/lgpd/info"))["contato"] == "privacidade@exemplo.com")
# exportação
c.post("/api/lojas/1/avaliacoes", json={"nota": 5, "comentario": "Muito bom, adorei o atendimento de todos."})
r = c.get("/api/lgpd/meus-dados"); d = json.loads(r.data)
t("exporta como anexo", "attachment" in r.headers["Content-Disposition"])
t("exporta conta e avaliação", d["conta"]["email"] == "maria@x.com" and len(d["avaliacoes"]) == 1 and len(d["consentimentos"]) == 4)
txt = r.data.decode()
t("sem hash de senha nem token", "senha_hash" not in txt and "token_hash" not in txt and "pbkdf2" not in txt and "scrypt" not in txt)
t("exporta só os meus", "Loja do João" in txt and "j@x.com" not in txt)
t("export exige login", cli().get("/api/lgpd/meus-dados").status_code == 401)
dl = json.loads(lj.get("/api/lgpd/meus-dados").data); t("comerciante exporta loja", dl["loja"][0]["nome_fantasia"] == "Loja do João" and "logo" not in dl["loja"][0])
# exclusão apaga tudo do titular
with A.app.app_context():
    con = banco.conexao(); uid = con.execute("SELECT id_usuario FROM usuario WHERE email='maria@x.com'").fetchone()[0]
r = c.delete("/api/conta", json={"senha": "senha1234", "confirmacao": "EXCLUIR"}); t("exclui conta", r.status_code == 200)
tabelas = ["avaliacao:id_cliente", "pedido:id_cliente", "sessao:id_usuario", "notificacao:id_usuario", "atividade:id_usuario", "carteira:id_usuario", "movimento_pontos:id_usuario", "voucher:id_usuario", "assinatura:id_usuario", "consentimento:id_usuario", "usuario:id_usuario"]
with A.app.app_context():
    con = banco.conexao()
    resto = {x: con.execute("SELECT COUNT(*) FROM %s WHERE %s = ?" % tuple(x.split(":")), (uid,)).fetchone()[0] for x in tabelas}
    sol = con.execute("SELECT id_usuario FROM solicitacao_titular WHERE tipo = 'exclusao'").fetchall()
t("nada sobra do titular", not any(resto.values()), resto)
t("registro de exclusão anônimo", len(sol) == 1 and sol[0][0] is None)
# retenção
with A.app.app_context():
    con = banco.conexao()
    con.execute("INSERT INTO atividade (id_usuario, acao, criada_em) SELECT id_usuario, 'velha', datetime('now','-400 days') FROM usuario LIMIT 1")
    con.execute("INSERT INTO atividade (id_usuario, acao) SELECT id_usuario, 'nova' FROM usuario LIMIT 1")
    con.execute("INSERT INTO tentativa (tipo, chave, criada_em) VALUES ('login','x',?)", (time.time() - 90000,)); con.commit()
lgpd.limpar_antigos()
with A.app.app_context():
    con = banco.conexao()
    t("apaga atividade vencida e mantém recente", con.execute("SELECT COUNT(*) FROM atividade WHERE acao='velha'").fetchone()[0] == 0 and con.execute("SELECT COUNT(*) FROM atividade WHERE acao='nova'").fetchone()[0] == 1)
    t("apaga tentativas antigas", con.execute("SELECT COUNT(*) FROM tentativa WHERE chave='x'").fetchone()[0] == 0)
h = cli().get("/api/config"); t("cabeçalhos de segurança", h.headers.get("Permissions-Policy") and h.headers["X-Frame-Options"] == "DENY")
for p in ("privacidade.html", "termos.html"): t("página " + p, cli().get("/html/" + p).status_code == 200)
print("OK", ok, "FALHAS", fail)
sys.exit(1 if fail else 0)
