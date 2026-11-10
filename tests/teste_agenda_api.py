"""Testes da agenda de eventos da cidade (API). Usa um banco temporário."""
import os, sys, tempfile
os.environ["DB_PATH"] = tempfile.mkdtemp() + "/t.db"; os.environ["SECRET_KEY"] = "x"
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "python"))
import app, agenda, banco  # noqa: E402

ok = fail = 0
def t(nome, cond, extra=""):
    global ok, fail
    if cond: ok += 1
    else: fail += 1; print("FALHOU:", nome, extra)

c = app.app.test_client()
d = c.get("/api/agenda").get_json()
ev = {e["titulo"]: e for e in d["eventos"]}
t("feira existe", "Feira de Frutas e Verduras" in ev)
t("motofest existe", "Motofest" in ev)
f, m = ev["Feira de Frutas e Verduras"], ev["Motofest"]
t("feira é de manhã e motofest à noite", f["periodo"] == "manha" and m["periodo"] == "noite")
t("os dois na quinta, na Estação", f["dia"] == m["dia"] == "Quinta" and "Estação" in f["local"] and "Estação" in m["local"])
t("são eventos distintos", f["id"] != m["id"])
t("sem horário inventado", f["horario"] is None and m["horario"] is None)
t("pendências registradas", len(f["pendencias"]) >= 1 and len(m["pendencias"]) >= 1)
t("sem foto inventada", f["foto"] is None and m["foto"] is None)
t("categorias", set(d["categorias"]) >= {"Feira", "Motos"})
agenda.semear()
t("semear não duplica", len(c.get("/api/agenda").get_json()["eventos"]) == len(d["eventos"]))
# novo evento só com uma linha no banco: aparece sem mexer em código
with app.app.app_context():
    con = banco.conexao()
    con.execute("INSERT INTO evento_cidade (slug, titulo, categoria, dia_semana, periodo, horario, local_nome, descricao) VALUES ('teste', 'Evento novo', 'Música', 'Sábado', 'tarde', '16:00', 'Praça', 'desc')")
    con.commit()
d2 = c.get("/api/agenda").get_json()
t("evento novo aparece", any(e["titulo"] == "Evento novo" and e["periodo_rotulo"] == "Tarde" for e in d2["eventos"]) and "Música" in d2["categorias"])
t("ordem por dia e período", [e["dia"] for e in d2["eventos"]] == sorted([e["dia"] for e in d2["eventos"]], key=["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"].index))
print("OK", ok, "FALHAS", fail)
