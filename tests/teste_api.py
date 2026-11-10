import os, sys, tempfile
os.environ["DB_PATH"] = tempfile.mktemp(suffix=".db")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "python"))
import app as A
c = A.app.test_client()
def ok(cond, msg):
    print(("OK   " if cond else "FALHA"), msg)
    if not cond: ok.f += 1
ok.f = 0
H = {d: {"fechado": d in ("dom",), "abre": "08:00", "fecha": "18:00"} for d in A.DIAS}
loja = dict(aceite=True, nome="Carlos Dono", email="carlos@email.com", telefone="(81) 99999-2222", senha="senha1234", confirmar_senha="senha1234",
  razao_social="Carlos Pastelaria LTDA", cnpj="11.222.333/0001-81", nome_fantasia="Pastelaria do Carlos", segmento="Alimentação",
  descricao="Pastéis e caldo de cana no centro.", cep="55012-000", rua="Rua Quinze de Novembro", numero="10", bairro="Centro",
  cidade="Caruaru", estado="pe", latitude=-8.2830, longitude=-35.9760, horarios=H, telefone_comercial="(81) 3721-0000",
  whatsapp="81999992222", instagram="@pastelcarlos", site="https://exemplo.com")
# validações
r = c.post("/api/cadastro/comerciante", json={}); ok(r.status_code==400 and "email" in r.json["campos"], "cadastro vazio devolve erros por campo")
r = c.post("/api/cadastro/comerciante", json=dict(loja, cnpj="11.222.333/0001-44")); ok(r.json["campos"].get("cnpj")=="CNPJ inválido.", "CNPJ inválido recusado")
r = c.post("/api/cadastro/comerciante", json=dict(loja, senha="abc", confirmar_senha="abd")); ok("senha" in r.json["campos"] and "confirmar_senha" in r.json["campos"], "senha fraca/diferente recusada")
r = c.post("/api/cadastro/comerciante", data="x"); ok(r.status_code==400, "não-JSON recusado")
# cadastro comerciante
r = c.post("/api/cadastro/comerciante", json=loja); ok(r.status_code==201 and r.json["usuario"]["perfil"]=="LOGISTA", "cadastro de comerciante")
r = c.post("/api/cadastro/comerciante", json=loja); ok(r.json["campos"].get("email"), "e-mail duplicado recusado")
# salvo no banco
import sqlite3; con = sqlite3.connect(os.environ["DB_PATH"])
row = con.execute("select u.perfil,u.senha_hash,l.cnpj,s.estado,s.latitude,s.longitude from usuario u join logista l on l.id_usuario=u.id_usuario join loja s on s.id_logista=u.id_usuario").fetchone()
ok(row and row[0]=="LOGISTA" and row[1]!="senha1234" and row[2]=="11222333000181" and row[3]=="PE" and row[4]==-8.283, f"dados gravados no banco (senha com hash): {row[0],row[2],row[3],row[4],row[5]}")
# painel
r = c.get("/api/minha-loja"); ok(r.status_code==200 and r.json["loja"]["nome"]=="Pastelaria do Carlos", "painel do comerciante lê a loja")
r = c.post("/api/minha-loja/vitrine", json={"nome":"Pastel de carne","valor":8.5}); ok(r.status_code==201, "adiciona item na vitrine"); item=r.json["id"]
r = c.post("/api/minha-loja/vitrine", json={"nome":"","valor":-1}); ok(r.status_code==400, "item inválido recusado")
r = c.post("/api/minha-loja/eventos", json={"nome":"Quinta do pastel","dia":"Quinta","horario":"18:00"}); ok(r.status_code==201, "anuncia evento"); ev=r.json["id"]
r = c.get("/api/eventos"); ok(len(r.json["eventos"])==1 and r.json["eventos"][0]["latitude"]==-8.283, "evento público herda localização da loja")
r = c.put("/api/minha-loja", json=dict(loja, descricao="Nova descrição da loja.", latitude=-8.29)); ok(r.status_code==200, "edita dados da loja")
ok(c.get("/api/minha-loja").json["loja"]["descricao"]=="Nova descrição da loja." and c.get("/api/minha-loja").json["loja"]["latitude"]==-8.29, "edição persistiu")
# permissões: comerciante não avalia nem reserva
idl = c.get("/api/minha-loja").json["loja"]["id"]
r = c.post(f"/api/lojas/{idl}/avaliacoes", json={"nota":5}); ok(r.status_code==403, "comerciante NÃO pode avaliar (403)")
c.post("/api/logout")
r = c.get("/api/minha-loja"); ok(r.status_code==401, "painel sem login = 401")
# usuário
r = c.post("/api/cadastro/usuario", json=dict(nome="Maria Silva", email="maria@email.com", telefone="81999991111", senha="maria1234", confirmar_senha="maria1234", aceite=True)); ok(r.status_code==201 and r.json["usuario"]["perfil"]=="CLIENTE", "cadastro de usuário")
r = c.get("/api/minha-loja"); ok(r.status_code==403, "usuário NÃO acessa painel do comerciante (403)")
r = c.post(f"/api/lojas/{idl}/avaliacoes", json={"nota":5,"comentario":"Ótimo!"}); ok(r.status_code==201, "usuário avalia")
r = c.post(f"/api/lojas/{idl}/avaliacoes", json={"nota":4,"comentario":"Mudei"}); ok(c.get(f"/api/lojas/{idl}/avaliacoes").json["avaliacoes"][0]["nota"]==4 and len(c.get(f"/api/lojas/{idl}/avaliacoes").json["avaliacoes"])==1, "reavaliar atualiza (1 por usuário)")
r = c.post(f"/api/lojas/{idl}/pedidos", json={"id_item":item}); ok(r.status_code==201, "usuário reserva item")
ok(len(c.get("/api/meus-pedidos").json["pedidos"])==1, "meus pedidos")
r = c.post(f"/api/lojas/{idl}/pedidos", json={"id_item":9999}); ok(r.status_code==404, "item inexistente = 404")
# login com perfil trocado
c.post("/api/logout")
r = c.post("/api/login", json={"email":"maria@email.com","senha":"maria1234","perfil":"LOGISTA"}); ok(r.status_code==403, "login: usuário escolhendo 'comerciante' é barrado")
r = c.post("/api/login", json={"email":"maria@email.com","senha":"errada","perfil":"CLIENTE"}); ok(r.status_code==401, "senha errada = 401")
r = c.post("/api/login", json={"email":"carlos@email.com","senha":"senha1234","perfil":"LOGISTA"}); ok(r.status_code==200, "login comerciante")
s = c.get("/api/minha-loja/estatisticas").json; ok(s["pedidos"]==1 and s["total_vendido"]==8.5 and s["nota_media"]==4.0 and s["avaliacoes_por_nota"]["4"]==1, f"estatísticas reais: {s['pedidos']} pedido, R${s['total_vendido']}, nota {s['nota_media']}")
r = c.get("/api/lojas?q=pastel"); ok(len(r.json["lojas"])==1 and r.json["lojas"][0]["nota"]==4.0, "busca de lojas")
r = c.get("/api/lojas?segmento=Cafeteria"); ok(len(r.json["lojas"])==0, "filtro por segmento")
r = c.delete(f"/api/minha-loja/vitrine/{item}"); ok(r.status_code==200 and not c.get("/api/minha-loja").json["loja"]["itens"], "remove item")
# segurança
ok(c.get("/python/app.py").status_code==404 and c.get("/.env").status_code==404 and c.get("/sql/banco.sql").status_code==404, "código/.env/sql não são servidos")
ok(c.get("/").status_code==200 and c.get("/html/tela.html").status_code==200 and c.get("/style/style.css").status_code==200, "telas são servidas")
print("FALHAS:", ok.f)
