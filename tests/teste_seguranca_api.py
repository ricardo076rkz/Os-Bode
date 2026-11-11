"""Testes de segurança geral: origem dos pedidos, erros sem vazar detalhes, acesso a arquivos internos."""
import os, sys, tempfile
os.environ["DB_PATH"] = tempfile.mkdtemp() + "/t.db"; os.environ["SECRET_KEY"] = "x"
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "python"))
import app as A  # noqa: E402
ok = fail = 0
def t(nome, cond, extra=""):
    global ok, fail
    if cond: ok += 1
    else: fail += 1; print("FALHOU:", nome, extra)
@A.app.get("/api/_quebra")
def _q():
    raise RuntimeError("segredo-interno")
A.app.config["PROPAGATE_EXCEPTIONS"] = False
c = A.app.test_client()
c2 = A.app.test_client()
cad = dict(nome="Maria Silva", email="m@x.com", telefone="81999998888", senha="senha1234", confirmar_senha="senha1234", aceite=True)
r = c.post("/api/cadastro/usuario", json=cad, headers={"Origin": "http://evil.example"})
t("origem de outro site é barrada", r.status_code == 403, r.data)
r = c.post("/api/cadastro/usuario", json=cad, headers={"Origin": "http://localhost"})
t("origem do próprio site passa", r.status_code == 201, r.data)
t("pedido sem Origin (servidor) passa", c.post("/api/login", json={"email": "m@x.com", "senha": "senha1234"}).status_code == 200)
t("GET nunca é barrado", c.get("/api/config", headers={"Origin": "http://evil.example"}).status_code in (200, 404))
for caminho in ("python/app.py", "python/.secret_key", ".env", ".git/config", "sql/banco.sql", "tests/teste_api.py", "../README.md", "html/../python/app.py", "html/../.env", "html/%2e%2e/python/app.py", "js/../python/schema.sql", "html/.env"):
    t("bloqueia " + caminho, c.get("/" + caminho).status_code in (404, 400))
# erro interno não vaza detalhes
r = c2.get("/api/_quebra")
t("500 é JSON genérico", r.status_code == 500 and "segredo-interno" not in r.get_data(as_text=True) and r.get_json()["erro"])
print("OK", ok, "FALHAS", fail)
sys.exit(1 if fail else 0)
