// Perfil - Nordestinando
const msg = pegarId("mensagem");
let conta = null;

pegarId("voltar").addEventListener("click", function (e) {
  e.preventDefault();
  if (conta && conta.perfil == "LOGISTA") window.location.href = "minha_loja.html";
  else window.location.href = "explorar.html";
});

function aviso(texto, tipo) {
  mostrarMensagem(msg, texto, tipo);
  msg.scrollIntoView({ block: "nearest" });
}

function desenharFoto() {
  const foto = pegarId("foto");
  foto.innerHTML = "";
  if (conta.avatar) {
    const img = document.createElement("img");
    img.alt = "";
    img.src = conta.avatar;
    foto.appendChild(img);
  } else {
    foto.textContent = inicial(conta.nome);
  }
  pegarId("remover-foto").classList.toggle("oculto", !conta.avatar);
}

function desenhar() {
  pegarId("nome-topo").textContent = conta.nome;
  pegarId("email-topo").textContent = conta.email;
  pegarId("etiqueta").textContent = conta.perfil == "LOGISTA" ? "Comerciante" : "Usuário";
  desenharFoto();
  const f = pegarId("form-dados");
  f.nome.value = conta.nome;
  f.email.value = conta.email;
  f.telefone.value = telefoneBR(conta.telefone);
  f.senha_atual.value = "";
  pegarId("criado").textContent = dataBR(conta.criado_em);

  const resumo = pegarId("resumo");
  resumo.innerHTML = "";
  const r = conta.resumo;
  const itens = conta.perfil == "LOGISTA"
    ? [["Loja", r.loja || "—"], ["CNPJ", r.cnpj ? r.cnpj : "não informado"]]
    : [["Avaliações feitas", r.avaliacoes], ["Pedidos", r.pedidos]];
  itens.forEach(function (i) {
    const caixa = criar("div", "mini");
    caixa.appendChild(criar("strong", "", i[1]));
    caixa.appendChild(criar("span", "", i[0]));
    resumo.appendChild(caixa);
  });
}

async function carregar() {
  try {
    conta = (await api("GET", "/api/conta")).conta;
  } catch (e) {
    if (e.status == 401) { window.location.href = "tela.html"; return; }
    pegarId("carregando").innerHTML = "";
    const m = criar("p", "mensagem erro", e.erro);
    pegarId("carregando").appendChild(m);
    return;
  }
  aplicarTema(conta.preferencias.tema);
  pegarId("carregando").classList.add("oculto");
  pegarId("conteudo").classList.remove("oculto");
  desenhar();
}

// ---------- abas
let atividadesCarregadas = false;
document.querySelectorAll(".aba").forEach(function (b) {
  b.addEventListener("click", function () {
    document.querySelectorAll(".aba").forEach(function (o) { o.setAttribute("aria-selected", o == b); });
    ["dados", "senha", "atividade"].forEach(function (nome) {
      pegarId("aba-" + nome).classList.toggle("oculto", nome != b.dataset.aba);
    });
    msg.classList.add("oculto");
    if (b.dataset.aba == "atividade") carregarAtividades();
  });
});

async function carregarAtividades() {
  const area = pegarId("atividades");
  area.innerHTML = "";
  area.appendChild(criar("div", "esqueleto"));
  try {
    const lista = (await api("GET", "/api/conta/atividades")).atividades;
    area.innerHTML = "";
    if (!lista.length) { area.appendChild(criar("p", "vazio", "Nenhuma atividade ainda.")); return; }
    lista.forEach(function (a) {
      const linha = criar("div", "lista-item");
      const t = criar("div");
      t.appendChild(criar("strong", "", a.acao));
      if (a.detalhe) t.appendChild(criar("small", "", a.detalhe));
      linha.appendChild(t);
      linha.appendChild(criar("small", "", dataHoraBR(a.criada_em)));
      area.appendChild(linha);
    });
  } catch (e) {
    area.innerHTML = "";
    area.appendChild(criar("p", "mensagem erro", e.erro));
  }
}

// ---------- envio com proteção contra clique duplo
function enviar(form, metodo, url, corpo, depois, textoBotao) {
  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    const botao = form.querySelector("button[type=submit]");
    mostrarErrosCampos(form, {});
    msg.classList.add("oculto");
    botao.disabled = true;
    botao.textContent = "Salvando...";
    try {
      const r = await api(metodo, url, corpo(form));
      depois(r, form);
    } catch (erro) {
      mostrarErrosCampos(form, erro.campos || {});
      aviso(erro.erro, "erro");
    } finally {
      botao.disabled = false;
      botao.textContent = textoBotao;
    }
  });
}

mascaraTelefone(pegarId("telefone"));
enviar(pegarId("form-dados"), "PATCH", "/api/conta", function (f) {
  return { nome: f.nome.value, email: f.email.value, telefone: f.telefone.value, senha_atual: f.senha_atual.value };
}, function (r) {
  conta = r.conta;
  desenhar();
  aviso("Dados salvos.", "ok");
}, "Salvar alterações");

enviar(pegarId("form-senha"), "POST", "/api/conta/senha", function (f) {
  return { senha_atual: f.senha_atual.value, senha: f.senha.value, confirmar_senha: f.confirmar_senha.value };
}, function (r, f) {
  f.reset();
  aviso("Senha alterada. Os outros aparelhos foram desconectados.", "ok");
}, "Alterar senha");

// ---------- foto
pegarId("trocar-foto").addEventListener("click", function () { pegarId("arquivo-foto").click(); });
pegarId("arquivo-foto").addEventListener("change", function (e) {
  const arquivo = e.target.files[0];
  e.target.value = "";
  if (!arquivo) return;
  if (!/^image\/(jpeg|png|webp)$/.test(arquivo.type)) { aviso("Use uma foto JPG, PNG ou WebP.", "erro"); return; }
  aviso("Enviando foto...", "info");
  reduzirFoto(arquivo, 400, async function (dataUrl) {
    if (!dataUrl) { aviso("Não consegui ler essa imagem.", "erro"); return; }
    try {
      const r = await api("POST", "/api/conta/foto", { imagem: dataUrl });
      conta.avatar = r.avatar;
      desenharFoto();
      aviso("Foto atualizada.", "ok");
    } catch (erro) { aviso(erro.erro, "erro"); }
  });
});
pegarId("remover-foto").addEventListener("click", async function () {
  try {
    await api("POST", "/api/conta/foto", { imagem: "" });
    conta.avatar = null;
    desenharFoto();
    aviso("Foto removida.", "ok");
  } catch (erro) { aviso(erro.erro, "erro"); }
});

pegarId("sair").addEventListener("click", async function () {
  try { await api("POST", "/api/logout"); } catch (e) {}
  window.location.href = "../index.html";
});

carregar();
