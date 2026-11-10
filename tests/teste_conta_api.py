import os, sys, tempfile, importlib
d = tempfile.mkdtemp()
os.environ["DB_PATH"] = d + "/t.db"; os.environ["SECRET_KEY"] = "x"
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "python"))
import app as A
ok = fail = 0
def t(nome, cond, extra=""):
    global ok, fail
    if cond: ok += 1
    else: fail += 1; print("FALHOU:", nome, extra)

def cli(): return A.app.test_client()
c = cli()
J = lambda r: r.get_json()
cad = dict(nome="Maria Silva", email="maria@x.com", telefone="81999998888", senha="senha1234", confirmar_senha="senha1234", aceite=True)
r = c.post("/api/cadastro/usuario", json=cad); t("cadastro", r.status_code == 201, r.data)
t("sem login 401", cli().get("/api/conta").status_code == 401)
t("sem login notif 401", cli().get("/api/notificacoes").status_code == 401)
r = c.get("/api/conta"); t("ver conta", J(r)["conta"]["email"] == "maria@x.com" and "senha_hash" not in r.data.decode())
# comerciante
c2 = cli()
com = dict(cad, nome="Joao Loja", email="joao@x.com")
# usa cadastro comerciante: descobrir payload
import inspect
loja = dict(nome_fantasia="Loja do João", segmento="Outros", descricao="Descrição da loja", cep="55012000", rua="Rua A", numero="1", bairro="Centro", cidade="Caruaru", estado="PE", latitude=-8.28, longitude=-35.97, telefone_comercial="81988887777",
            horarios={k: {"fechado": False, "abre": "08:00", "fecha": "18:00"} for k in A.DIAS})
r = c2.post("/api/cadastro/comerciante", json=dict(com, **loja)); t("cad comerciante", r.status_code == 201, r.data)
# permissões
t("cliente nao acessa minha-loja", c.get("/api/minha-loja").status_code == 403)
t("logista nao avalia", c2.post("/api/lojas/1/avaliacoes", json={"nota": 5}).status_code == 403)
# editar perfil
r = c.patch("/api/conta", json=dict(nome="Maria S", email="maria@x.com", telefone="81999990000")); t("editar", r.status_code == 200 and J(r)["conta"]["nome"] == "Maria S", r.data)
r = c.patch("/api/conta", json=dict(nome="Ma", email="x", telefone="1")); t("editar valida", r.status_code == 400 and len(J(r)["campos"]) == 3)
r = c.patch("/api/conta", json=dict(nome="Maria S", email="novo@x.com", telefone="81999990000")); t("email exige senha", r.status_code == 400 and "senha_atual" in J(r)["campos"])
r = c.patch("/api/conta", json=dict(nome="Maria S", email="joao@x.com", telefone="81999990000", senha_atual="senha1234")); t("email duplicado", r.status_code == 400 and "email" in J(r)["campos"], r.data)
r = c.patch("/api/conta", json=dict(nome="Maria S", email="novo@x.com", telefone="81999990000", senha_atual="senha1234")); t("email ok", r.status_code == 200)
# foto
png = "data:image/png;base64,iVBORw0KGgo="
r = c.post("/api/conta/foto", json={"imagem": png}); t("foto", r.status_code == 200 and J(r)["avatar"] == png)
r = c.post("/api/conta/foto", json={"imagem": "data:text/html;base64,AAAA"}); t("foto invalida", r.status_code == 400)
r = c.post("/api/conta/foto", json={"imagem": "<script>"}); t("foto xss", r.status_code == 400)
# preferências
r = c.put("/api/conta/preferencias", json={"tema": "escuro", "notif": {"eventos": False}, "privacidade": {"nome_nas_avaliacoes": False}}); t("prefs", J(r)["preferencias"]["tema"] == "escuro" and not J(r)["preferencias"]["notif"]["eventos"], r.data)
r = c.put("/api/conta/preferencias", json={"tema": "rosa"}); t("tema invalido", r.status_code == 400)
# avaliação anônima + notificação ao logista
t('boas-vindas logista', J(c2.get('/api/notificacoes'))['nao_lidas']==1); c2.post('/api/notificacoes/lidas'); c2.delete('/api/notificacoes')
r = c.post("/api/lojas/1/avaliacoes", json={"nota": 4, "comentario": "ok"}); t("avaliar", r.status_code == 201, r.data)
av = J(c.get("/api/lojas/1/avaliacoes"))["avaliacoes"]; t("anonimo", av[0]["cliente"] == "Anônimo", av)
n = J(c2.get("/api/notificacoes")); t("logista recebeu notif", n["nao_lidas"] == 1 and "Nova avaliação" in n["notificacoes"][0]["titulo"] and "Um cliente" in n["notificacoes"][0]["mensagem"], n)
# cliente isolado das notificações do logista
nid = n["notificacoes"][0]["id"]
t("outro usuario nao marca", c.post(f"/api/notificacoes/{nid}/lida").status_code == 404)
t("outro usuario nao exclui", c.delete(f"/api/notificacoes/{nid}").status_code == 404)
t("marcar lida", c2.post(f"/api/notificacoes/{nid}/lida").status_code == 200 and J(c2.get("/api/notificacoes/contagem"))["nao_lidas"] == 0)
# pedido: item na vitrine
r = c2.post("/api/minha-loja/vitrine", json={"nome": "Cuscuz", "valor": 5}); t("vitrine", r.status_code in (200, 201), r.data)
iid = J(c2.get("/api/minha-loja"))["loja"]["itens"][0]["id"]
r = c.post("/api/lojas/1/pedidos", json={"id_item": iid}); t("pedido", r.status_code == 201, r.data)
n = J(c2.get("/api/notificacoes")); t("notif pedido", n["nao_lidas"] == 1)
r = c2.post("/api/notificacoes/lidas"); t("todas lidas", J(r)["marcadas"] == 1)
r = c2.delete("/api/notificacoes"); t("limpar lidas", J(r)["excluidas"] == 2, r.data)
# evento: cliente tem eventos desligado -> não recebe
r = c2.post("/api/minha-loja/eventos", json={"nome": "Forró", "dia": "Sábado", "horario": "20:00"}); t("evento", r.status_code == 201, r.data)
nc = J(c.get("/api/notificacoes"))["notificacoes"]; t("pref eventos respeitada", not any(x["categoria"] == "eventos" for x in nc), nc)
c.put("/api/conta/preferencias", json={"notif": {"eventos": True}})
c2.post("/api/minha-loja/eventos", json={"nome": "Quadrilha", "dia": "Domingo", "horario": "19:00"})
nc = J(c.get("/api/notificacoes"))["notificacoes"]; t("evento notifica", any(x["categoria"] == "eventos" for x in nc))
# senha
r = c.post("/api/conta/senha", json=dict(senha_atual="errada", senha="novaSenha1", confirmar_senha="novaSenha1")); t("senha atual errada", r.status_code == 400 and "senha_atual" in J(r)["campos"])
r = c.post("/api/conta/senha", json=dict(senha_atual="senha1234", senha="abc", confirmar_senha="abc")); t("senha fraca", r.status_code == 400)
# sessões
c3 = cli(); r = c3.post("/api/login", json=dict(email="novo@x.com", senha="senha1234", perfil="CLIENTE")); t("login 2o aparelho", r.status_code == 200, r.data)
s = J(c.get("/api/conta/sessoes"))["sessoes"]; t("2 sessoes", len(s) == 2 and sum(x["atual"] for x in s) == 1, s)
outra = [x for x in s if not x["atual"]][0]["id"]
atual = [x for x in s if x["atual"]][0]["id"]
t("nao encerra atual", c.delete(f"/api/conta/sessoes/{atual}").status_code == 400)
t("outro usuario nao encerra sessao alheia", c2.delete(f"/api/conta/sessoes/{outra}").status_code == 404)
t("encerrar outra", c.delete(f"/api/conta/sessoes/{outra}").status_code == 200)
t("sessao encerrada perde acesso", c3.get("/api/conta").status_code == 401)
c3.post("/api/login", json=dict(email="novo@x.com", senha="senha1234"))
r = c.post("/api/conta/senha", json=dict(senha_atual="senha1234", senha="novaSenha1", confirmar_senha="novaSenha1")); t("trocar senha", r.status_code == 200, r.data)
t("troca de senha derruba outros", c3.get("/api/conta").status_code == 401 and c.get("/api/conta").status_code == 200)
t("login senha antiga falha", cli().post("/api/login", json=dict(email="novo@x.com", senha="senha1234")).status_code == 401)
t("login senha nova", cli().post("/api/login", json=dict(email="novo@x.com", senha="novaSenha1")).status_code == 200)
ativ = J(c.get("/api/conta/atividades"))["atividades"]; t("historico", len(ativ) >= 5 and any(a["acao"] == "Senha alterada" for a in ativ))
# rate limit
cr = cli()
for i in range(5): cr.post("/api/login", json=dict(email="maria@x.com", senha="x"))
r = cr.post("/api/login", json=dict(email="novo@x.com", senha="novaSenha1")); t("login ok com outro email", r.status_code == 200)
r = cr.post("/api/login", json=dict(email="maria@x.com", senha="x")); t("bloqueio 429", r.status_code in (401, 429))
r = cli().post("/api/login", json=dict(email="novo@x.com", senha="errada"))
for i in range(6): r = cli().post("/api/login", json=dict(email="alvo@x.com", senha="x"))
t("429 apos 5 erros", r.status_code == 429, r.status_code)
# recuperação
r1 = cli().post("/api/senha/esqueci", json={"email": "novo@x.com"}); r2 = cli().post("/api/senha/esqueci", json={"email": "naoexiste@x.com"})
t("esqueci nao revela", r1.status_code == 200 and J(r1) == J(r2))
t("redefinir token falso", cli().post("/api/senha/redefinir", json=dict(token="abc", senha="Outra1234", confirmar_senha="Outra1234")).status_code == 400)
import sqlite3
con = sqlite3.connect(os.environ["DB_PATH"])
# pega o token do link impresso: gerar novo e capturar
import io, contextlib
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    cli().post("/api/senha/esqueci", json={"email": "novo@x.com"})
tok = buf.getvalue().split("token=")[1].split()[0]
t("token nao guardado em claro", con.execute("SELECT COUNT(*) FROM redefinicao_senha WHERE token_hash = ?", (tok,)).fetchone()[0] == 0)
r = cli().post("/api/senha/redefinir", json=dict(token=tok, senha="Outra1234", confirmar_senha="Outra1234")); t("redefinir", r.status_code == 200, r.data)
t("token usa uma vez", cli().post("/api/senha/redefinir", json=dict(token=tok, senha="Outra5678", confirmar_senha="Outra5678")).status_code == 400)
t("login nova senha", cli().post("/api/login", json=dict(email="novo@x.com", senha="Outra1234")).status_code == 200)
con.execute("UPDATE redefinicao_senha SET usada=0, expira_em=1"); con.commit()
t("token expirado", cli().post("/api/senha/redefinir", json=dict(token=tok, senha="Outra5678", confirmar_senha="Outra5678")).status_code == 400)
# excluir conta
cx = cli(); cx.post("/api/login", json=dict(email="novo@x.com", senha="Outra1234"))
r = cx.delete("/api/conta", json=dict(senha="errada", confirmacao="EXCLUIR")); t("excluir senha errada", r.status_code == 400)
r = cx.delete("/api/conta", json=dict(senha="Outra1234", confirmacao="nao")); t("excluir sem confirmacao", r.status_code == 400)
r = cx.delete("/api/conta", json=dict(senha="Outra1234", confirmacao="excluir")); t("excluir", r.status_code == 200, r.data)
t("conta sumiu", con.execute("SELECT COUNT(*) FROM usuario WHERE email='novo@x.com'").fetchone()[0] == 0 and cx.get("/api/conta").status_code == 401)
t("avaliacoes removidas", con.execute("SELECT COUNT(*) FROM avaliacao").fetchone()[0] == 0)
# logout
c2.post("/api/logout"); t("logout", c2.get("/api/conta").status_code == 401)
# cabeçalhos
r = cli().get("/api/config"); t("headers", r.headers.get("X-Frame-Options") == "DENY" and r.headers["Cache-Control"] == "no-store")
t("estatico sem vazar python", cli().get("/python/app.py").status_code == 404)
print("OK", ok, "FALHAS", fail)
