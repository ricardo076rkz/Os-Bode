// Central de notificações - Nordestinando
let filtro = "todas";
let carregou = false;
const lista = pegarId("lista");
const msg = pegarId("mensagem");

pegarId("voltar").addEventListener("click", function (e) {
  e.preventDefault();
  if (document.referrer && history.length > 1) history.back();
  else window.location.href = "explorar.html";
});

function esqueletos() {
  lista.innerHTML = "";
  for (let i = 0; i < 3; i++) lista.appendChild(criar("div", "esqueleto"));
}

function vazio(titulo, texto) {
  const caixa = criar("div", "estado-vazio");
  caixa.appendChild(criar("strong", "", titulo));
  caixa.appendChild(criar("span", "", texto));
  return caixa;
}

function cartao(n) {
  const el = criar("article", "notif" + (n.lida ? "" : " nao-lida"));
  const corpo = criar("div", "corpo");
  let topo;
  if (n.link) {
    topo = criar("a");
    topo.href = n.link;
    topo.addEventListener("click", function () {
      if (!n.lida) api("POST", "/api/notificacoes/" + n.id + "/lida").catch(function () {});
    });
  } else {
    topo = criar("div");
  }
  topo.appendChild(criar("div", "titulo", n.titulo));
  topo.appendChild(criar("p", "", n.mensagem));
  corpo.appendChild(topo);
  const rodape = criar("small");
  rodape.appendChild(criar("span", "categoria", n.rotulo));
  rodape.appendChild(document.createTextNode(dataHoraBR(n.criada_em)));
  corpo.appendChild(rodape);
  el.appendChild(corpo);

  const acoes = criar("div", "acoes-notif");
  if (!n.lida) {
    const ler = criar("button");
    ler.type = "button";
    ler.title = "Marcar como lida";
    ler.setAttribute("aria-label", "Marcar como lida");
    ler.appendChild(icone("check"));
    ler.addEventListener("click", function () { agir("POST", "/api/notificacoes/" + n.id + "/lida"); });
    acoes.appendChild(ler);
  }
  const apagar = criar("button");
  apagar.type = "button";
  apagar.title = "Excluir";
  apagar.setAttribute("aria-label", "Excluir notificação");
  apagar.appendChild(icone("lixeira"));
  apagar.addEventListener("click", function () { agir("DELETE", "/api/notificacoes/" + n.id); });
  acoes.appendChild(apagar);
  el.appendChild(acoes);
  return el;
}

async function agir(metodo, url, textoOk) {
  msg.classList.add("oculto");
  try {
    const r = await api(metodo, url);
    if (textoOk) {
      const n = r.marcadas !== undefined ? r.marcadas : r.excluidas;
      mostrarMensagem(msg, n ? textoOk.replace("{n}", n) : "Nada para fazer aqui.", "ok");
    }
    await carregar(true);
  } catch (e) {
    mostrarMensagem(msg, e.erro, "erro");
  }
}

async function carregar(silencioso) {
  if (!silencioso && !carregou) esqueletos();
  try {
    const d = await api("GET", "/api/notificacoes" + (filtro == "novas" ? "?so_nao_lidas=1" : ""));
    carregou = true;
    pegarId("qtd-novas").textContent = d.nao_lidas ? "(" + d.nao_lidas + ")" : "";
    lista.innerHTML = "";
    if (!d.notificacoes.length) {
      lista.appendChild(filtro == "novas" ? vazio("Tudo em dia", "Você não tem notificações novas.") : vazio("Nenhuma notificação ainda", "Avisos sobre avaliações, pedidos, eventos e segurança da sua conta aparecem aqui."));
      return;
    }
    d.notificacoes.forEach(function (n) { lista.appendChild(cartao(n)); });
  } catch (e) {
    if (e.status == 401) { window.location.href = "tela.html"; return; }
    lista.innerHTML = "";
    lista.appendChild(vazio("Não foi possível carregar", e.erro));
    const tentar = criar("button", "botao contorno", "Tentar de novo");
    tentar.type = "button";
    tentar.addEventListener("click", function () { carregar(); });
    lista.appendChild(tentar);
  }
}

function escolher(f) {
  filtro = f;
  pegarId("aba-todas").setAttribute("aria-selected", f == "todas");
  pegarId("aba-novas").setAttribute("aria-selected", f == "novas");
  carregar();
}
pegarId("aba-todas").addEventListener("click", function () { escolher("todas"); });
pegarId("aba-novas").addEventListener("click", function () { escolher("novas"); });
pegarId("marcar-todas").addEventListener("click", function () { agir("POST", "/api/notificacoes/lidas", "{n} notificação(ões) marcada(s) como lida(s)."); });
pegarId("limpar-lidas").addEventListener("click", function () {
  if (confirm("Apagar todas as notificações já lidas?")) agir("DELETE", "/api/notificacoes", "{n} notificação(ões) apagada(s).");
});

carregar();
// "tempo real": confere novidades a cada 30 segundos enquanto a aba está aberta
setInterval(function () { if (!document.hidden) carregar(true); }, 30000);
