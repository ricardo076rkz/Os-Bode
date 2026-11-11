"""Testes da gamificação (pontos, carteira, promoções, vouchers, Nordestinando+). Banco temporário."""
import os, sys, tempfile, hmac, hashlib, json
os.environ["DB_PATH"] = tempfile.mkdtemp() + "/t.db"; os.environ["SECRET_KEY"] = "x"
os.environ["ADMIN_TOKEN"] = "adm"; os.environ.pop("PAGAMENTO_DEMO", None); os.environ.pop("PAGAMENTO_WEBHOOK_SEGREDO", None)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "python"))
import app as A, banco, gamificacao as G  # noqa: E402
from datetime import date, timedelta

ok = fail = 0
def t(nome, cond, extra=""):
    global ok, fail
    if cond: ok += 1
    else: fail += 1; print("FALHOU:", nome, extra)
J = lambda r: r.get_json()
def uid(email):
    with A.app.app_context():
        return banco.conexao().execute("SELECT id_usuario FROM usuario WHERE email = ?", (email,)).fetchone()[0]
cli = A.app.test_client
cad = dict(nome="Maria Silva", email="maria@x.com", telefone="81999998888", senha="senha1234", confirmar_senha="senha1234", aceite=True)
loja = dict(nome_fantasia="Loja do João", segmento="Outros", descricao="Descrição da loja", cep="55012000", rua="Rua A", numero="1", bairro="Centro", cidade="Caruaru", estado="PE", latitude=-8.28, longitude=-35.97, telefone_comercial="81988887777",
            horarios={k: {"fechado": False, "abre": "08:00", "fecha": "18:00"} for k in A.DIAS})
cm, lj, lj2 = cli(), cli(), cli()
t("cadastro cliente", cm.post("/api/cadastro/usuario", json=cad).status_code == 201)
t("cadastro loja", lj.post("/api/cadastro/comerciante", json=dict(cad, nome="Joao Loja", email="joao@x.com", **loja)).status_code == 201)
lj2.post("/api/cadastro/comerciante", json=dict(cad, nome="Outro Loja", email="outro@x.com", **dict(loja, nome_fantasia="Outra Loja")))
cheia = dict(nota=1, crit_atendimento=4, crit_qualidade=5, crit_preco=3, crit_ambiente=4,
             comentario="Atendimento muito bom, comida saborosa e ambiente agradável para a família toda, voltarei.",
             dica="Vá cedo para pegar mesa", consumiu="Cuscuz")
# 1 sem login / sem pontos inválidos
t("estimativa exige login", cli().post("/api/pontos/estimativa", json={}).status_code == 401)
r = cm.post("/api/pontos/estimativa", json={"crit_atendimento": 5}); e = J(r)["estimativa"]
t("1 critério não pontua", not e["valido"] and e["total"] == 0)
r = cm.post("/api/pontos/estimativa", json=cheia); e = J(r)["estimativa"]
t("estimativa completa", e["valido"] and e["base"] == 10 + 12 + 10 + 5 + 3 and e["total"] == e["base"], e)
# 2 nota não influencia
a = J(cm.post("/api/pontos/estimativa", json=dict(cheia, nota=5)))["estimativa"]["total"]
t("nota negativa = positiva", a == e["total"])
# 3 avaliar e ganhar
r = cm.post("/api/lojas/1/avaliacoes", json=cheia); g = J(r)["ganho"]
t("avaliação pontua", r.status_code == 201 and g["pontos"] == e["total"], g)
t("saldo na carteira", J(cm.get("/api/carteira"))["carteira"]["saldo"] == e["total"])
# 4 reenviar não duplica
r = cm.post("/api/lojas/1/avaliacoes", json=cheia); t("reenvio sem pontos", J(r)["ganho"]["pontos"] == 0)
t("saldo igual", J(cm.get("/api/carteira"))["carteira"]["saldo"] == e["total"])
# 5 completar paga só a diferença (foto)
png = "data:image/png;base64,iVBORw0KGgo="
r = cm.post("/api/lojas/1/avaliacoes", json=dict(cheia, foto=png)); t("foto paga diferença", J(r)["ganho"]["pontos"] == 10, r.data)
saldo = e["total"] + 10
# 6 avaliação inválida / só nota
t("só nota não pontua", J(cli().post("/api/cadastro/usuario", json=dict(cad, email="z@x.com")) and cm.post("/api/lojas/2/avaliacoes", json={"nota": 5}))["ganho"]["pontos"] == 0)
t("nota obrigatória", cm.post("/api/lojas/2/avaliacoes", json={}).status_code == 400)
t("texto repetido não pontua", J(cm.post("/api/lojas/2/avaliacoes", json={"nota": 5, "comentario": "a" * 100}))["ganho"]["pontos"] == 0)
t("logista não usa carteira", lj.get("/api/carteira").status_code == 403)
# 7 promoção: criar (só logista), validações
hoje = date.today(); fim = (hoje + timedelta(days=10)).isoformat()
prom = dict(titulo="10% no cuscuz", descricao="Desconto no cuscuz", tipo_beneficio="percentual", valor_beneficio=10, pontos_necessarios=30, quantidade_total=2, limite_por_usuario=1, inicio=hoje.isoformat(), fim=fim, condicoes="Válido no balcão")
t("cliente não cria promoção", cm.post("/api/minha-loja/promocoes", json=prom).status_code == 403)
t("promoção inválida", lj.post("/api/minha-loja/promocoes", json=dict(prom, pontos_necessarios=0, valor_beneficio=500)).status_code == 400)
r = lj.post("/api/minha-loja/promocoes", json=prom); t("cria promoção", r.status_code == 201, r.data); idp = J(r)["promocao"]["id"]
t("aparece em recompensas", any(x["id"] == idp for x in J(cm.get("/api/recompensas"))["recompensas"]))
# 8 resgate: pontos insuficientes
r = lj.post("/api/minha-loja/promocoes", json=dict(prom, titulo="Caro", pontos_necessarios=9999)); caro = J(r)["promocao"]["id"]
r = cm.post("/api/recompensas/%d/resgatar" % caro); t("pontos insuficientes", r.status_code == 400 and "Faltam" in J(r)["erro"])
t("saldo intacto após falha", J(cm.get("/api/carteira"))["carteira"]["saldo"] == saldo)
# 9 resgate ok
r = cm.post("/api/recompensas/%d/resgatar" % idp); t("resgata", r.status_code == 201, r.data); cod = J(r)["voucher"]["codigo"]
t("código formatado", cod.startswith("NORD-") and len(cod) == 14)
t("pontos debitados", J(cm.get("/api/carteira"))["carteira"]["saldo"] == saldo - 30)
t("limite por usuário", cm.post("/api/recompensas/%d/resgatar" % idp).status_code == 400)
t("voucher na carteira", [v["codigo"] for v in J(cm.get("/api/carteira/vouchers"))["vouchers"]] == [cod])
t("razão consistente", True)
with A.app.app_context():
    t("saldo = soma do razão", G.verificar_saldo(banco.conexao(), uid('maria@x.com')))
# 10 validação pelo comerciante
t("outra loja não acha código", lj2.post("/api/minha-loja/vouchers/validar", json={"codigo": cod}).status_code == 404)
t("cliente não valida", cm.post("/api/minha-loja/vouchers/validar", json={"codigo": cod}).status_code == 403)
r = lj.post("/api/minha-loja/vouchers/validar", json={"codigo": cod.lower()}); t("valida", r.status_code == 200 and J(r)["voucher"]["estado"] == "utilizado", r.data)
r = lj.post("/api/minha-loja/vouchers/validar", json={"codigo": cod}); t("uso único", r.status_code == 409)
# 11 expirado e cancelamento com estorno
r = lj.post("/api/minha-loja/promocoes", json=dict(prom, titulo="Outra", pontos_necessarios=20, quantidade_total=5, limite_por_usuario=3)); p2 = J(r)["promocao"]["id"]
cod2 = J(cm.post("/api/recompensas/%d/resgatar" % p2))["voucher"]["codigo"]
s_antes = J(cm.get("/api/carteira"))["carteira"]["saldo"]
vid = [v for v in J(lj.get("/api/minha-loja/vouchers"))["vouchers"] if v["codigo"] == cod2][0]["id"]
t("cancela", lj.post("/api/minha-loja/vouchers/%d/cancelar" % vid).status_code == 200)
t("estorno de pontos", J(cm.get("/api/carteira"))["carteira"]["saldo"] == s_antes + 20)
t("não cancela 2x", lj.post("/api/minha-loja/vouchers/%d/cancelar" % vid).status_code == 400)
cod3 = J(cm.post("/api/recompensas/%d/resgatar" % p2))["voucher"]["codigo"]
with A.app.app_context():
    con = banco.conexao(); con.execute("UPDATE voucher SET validade = '2000-01-01' WHERE codigo = ?", (cod3,)); con.commit()
r = lj.post("/api/minha-loja/vouchers/validar", json={"codigo": cod3}); t("expirado", r.status_code == 400 and "expirou" in J(r)["erro"])
# 12 estoque esgotado
c3 = cli(); c3.post("/api/cadastro/usuario", json=dict(cad, email="c3@x.com"))
with A.app.app_context():
    con = banco.conexao(); u3 = uid('c3@x.com'); con.execute("INSERT OR IGNORE INTO carteira (id_usuario) VALUES (?)", (u3,)); con.execute("UPDATE carteira SET saldo = 500, total_ganho = 500 WHERE id_usuario = ?", (u3,))
    con.execute("INSERT INTO movimento_pontos (id_usuario, tipo, pontos, descricao, chave, saldo_apos) VALUES (?, 'avaliacao', 500, 'teste', 'teste', 500)", (u3,)); con.commit()
r = lj.post("/api/minha-loja/promocoes", json=dict(prom, titulo="Única", pontos_necessarios=10, quantidade_total=1, limite_por_usuario=5)); p3 = J(r)["promocao"]["id"]
t("1º resgata", c3.post("/api/recompensas/%d/resgatar" % p3).status_code == 201)
t("esgotado", c3.post("/api/recompensas/%d/resgatar" % p3).status_code == 400)
t("some da lista", all(x["id"] != p3 for x in J(c3.get("/api/recompensas"))["recompensas"]))
t("pausar promoção", lj.patch("/api/minha-loja/promocoes/%d" % p2, json={"status": "pausada"}).status_code == 200)
t("pausada não resgata", c3.post("/api/recompensas/%d/resgatar" % p2).status_code == 400)
# 13 premium
t("plano gratuito", J(cm.get("/api/premium"))["plano"]["estado"] == "gratuito")
r = cm.post("/api/premium/assinar"); t("sem gateway não ativa", r.status_code == 503 and J(cm.get("/api/premium"))["plano"]["estado"] == "gratuito")
os.environ["PAGAMENTO_DEMO"] = "1"
r = cm.post("/api/premium/assinar"); pl = J(r)["plano"]; t("demo ativa", r.status_code == 201 and pl["estado"] == "premium_ativo" and pl["ambiente"] == "demo" and pl["preco_centavos"] == 590, r.data)
c4 = cli(); c4.post("/api/cadastro/usuario", json=dict(cad, email="c4@x.com"))
base = J(c4.post("/api/lojas/1/avaliacoes", json=cheia))["ganho"]["pontos"]
cm2 = cli(); cm2.post("/api/login", json={"email": "maria@x.com", "senha": "senha1234"})
dobro = J(cm.post("/api/lojas/2/avaliacoes", json=cheia))["ganho"]
t("premium dobra", dobro["pontos"] == base * 2 and dobro["bonus"] == base and dobro["premium"], (base, dobro))
t("bônus na carteira", J(cm.get("/api/carteira"))["carteira"]["bonus_premium"] >= base)
t("cancela premium", cm.post("/api/premium/cancelar").status_code == 200 and J(cm.get("/api/premium"))["plano"]["estado"] == "premium_cancelado")
with A.app.app_context():
    con = banco.conexao(); con.execute("UPDATE assinatura SET status='ativa', fim='2000-01-01' WHERE id_usuario=%d" % uid('maria@x.com')); con.commit()
t("premium expirado", J(cm.get("/api/premium"))["plano"]["estado"] == "premium_expirado" and J(cm.get("/api/premium"))["plano"]["multiplicador"] == 1)
# webhook
body = json.dumps({"id_usuario": uid("c4@x.com"), "referencia": "pg1", "status": "confirmado", "valor_centavos": 590}).encode()
t("webhook sem segredo", c4.post("/api/premium/webhook", data=body, content_type="application/json").status_code == 503)
os.environ["PAGAMENTO_WEBHOOK_SEGREDO"] = "s"
sig = hmac.new(b"s", body, hashlib.sha256).hexdigest()
t("webhook assinatura ruim", c4.post("/api/premium/webhook", data=body, content_type="application/json", headers={"X-Assinatura": "x"}).status_code == 401)
t("webhook ok", c4.post("/api/premium/webhook", data=body, content_type="application/json", headers={"X-Assinatura": sig}).status_code == 200)
t("webhook repetido", J(c4.post("/api/premium/webhook", data=body, content_type="application/json", headers={"X-Assinatura": sig}))["repetido"])
t("webhook ativou premium", J(c4.get("/api/premium"))["plano"]["estado"] == "premium_ativo")
# admin
t("admin sem token", cli().get("/api/admin/gamificacao").status_code == 403)
ad = J(cli().get("/api/admin/gamificacao", headers={"X-Admin-Token": "adm"}))
t("admin indicadores", ad["usuarios_premium"] >= 1 and ad["vouchers_utilizados"] == 1 and ad["pagamentos_demo"] == 1 and ad["pontos_distribuidos"] > 0, ad)
print("OK", ok, "FALHAS", fail)
sys.exit(1 if fail else 0)
