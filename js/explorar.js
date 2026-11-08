// Explorar cidade: lojas e eventos reais do banco, no mapa e na lista
// (depende de comum.js, api.js e mapa.js)

let usuario = null;
let lojas = [];
let segmentoEscolhido = "Todos";
let mapa = null;
const marcadores = {}; // id da loja -> marcador
const msg = pegarId("mensagem");

// ---------- conta no canto de cima ----------
function mostrarConta() {
  const area = pegarId("conta");
  area.innerHTML = "";
  if (usuario) {
    area.appendChild(criar("span", "detalhe-conta", usuario.nome.split(" ")[0] + " · "));
    const sair = criar("a", "link-topo", "Sair");
    sair.href = "#";
    sair.addEventListener("click", async function (e) {
      e.preventDefault();
      await api("POST", "/api/logout");
      window.location.reload();
    });
    area.appendChild(sair);
  } else {
    const entrar = criar("a", "link-topo", "Entrar");
    entrar.href = "tela.html";
    area.appendChild(entrar);
  }
  pegarId("meus-pedidos").classList.toggle("oculto", !(usuario && usuario.perfil == "CLIENTE"));
}

// ---------- mapa e marcadores ----------
function conteudoJanela(l) {
  const caixa = criar("div", "balao");
  caixa.appendChild(criar("strong", "", l.nome));
  caixa.appendChild(criar("div", "", l.segmento + " · ★ " + notaFormatada(l.nota)));
  caixa.appendChild(criar("div", "", l.endereco));
  const hoje = horarioHoje(l.horarios);
  if (hoje) caixa.appendChild(criar("div", "", hoje));
  const rota = criar("a", "", "Como chegar");
  rota.href = linkRota(l.latitude, l.longitude);
  rota.target = "_blank";
  rota.rel = "noopener";
  caixa.appendChild(rota);
  return caixa;
}

function abrirNoMapa(l) {
  const m = marcadores[l.id];
  if (!mapa || !m) return;
  mapa.setView(m.getLatLng(), 17);
  m.openPopup();
}

function desenharMarcadores(lista) {
  if (!mapa) return;
  Object.keys(marcadores).forEach(function (id) {
    marcadores[id].remove();
    delete marcadores[id];
  });
  const pontos = [];
  lista.forEach(function (l) {
    // o balão abre ao clicar no marcador
    marcadores[l.id] = L.marker([l.latitude, l.longitude], { title: l.nome })
      .addTo(mapa)
      .bindPopup(conteudoJanela(l));
    pontos.push([l.latitude, l.longitude]);
  });
  if (pontos.length > 1) mapa.fitBounds(pontos, { padding: [40, 40] });
  if (pontos.length == 1) mapa.setView(pontos[0], 16);
}

// ---------- lojas ----------
async function carregarLojas() {
  const busca = pegarId("busca").value.trim();
  const params = new URLSearchParams();
  if (busca) params.set("q", busca);
  if (segmentoEscolhido != "Todos") params.set("segmento", segmentoEscolhido);
  const dados = await api("GET", "/api/lojas?" + params.toString());
  lojas = dados.lojas;
  mostrarLojas();
  desenharMarcadores(lojas);
}

async function mostrarChips() {
  const config = await api("GET", "/api/config");
  const chips = pegarId("chips");
  chips.innerHTML = "";
  ["Todos"].concat(config.segmentos).forEach(function (seg) {
    const chip = criar("button", "chip", seg);
    chip.type = "button";
    if (seg == segmentoEscolhido) chip.classList.add("ativo");
    chip.addEventListener("click", function () {
      segmentoEscolhido = seg;
      mostrarChips();
      carregarLojas();
    });
    chips.appendChild(chip);
  });
}

function formularioAvaliar(l) {
  const form = criar("form", "avaliar");
  const select = document.createElement("select");
  [5, 4, 3, 2, 1].forEach(function (n) {
    const o = document.createElement("option");
    o.value = n;
    o.textContent = n + (n == 1 ? " estrela" : " estrelas");
    select.appendChild(o);
  });
  const texto = document.createElement("input");
  texto.type = "text";
  texto.placeholder = "Comentário (opcional)";
  texto.maxLength = 300;
  const enviar = criar("button", "botao", "Enviar avaliação");
  enviar.type = "submit";
  form.appendChild(select);
  form.appendChild(texto);
  form.appendChild(enviar);

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    try {
      await api("POST", "/api/lojas/" + l.id + "/avaliacoes", { nota: select.value, comentario: texto.value });
      mostrarMensagem(msg, "Avaliação enviada. Obrigado!", "ok");
      carregarLojas();
    } catch (erro) {
      mostrarMensagem(msg, erro.erro, "erro");
    }
  });
  return form;
}

function mostrarLojas() {
  const lista = pegarId("lista-lojas");
  lista.innerHTML = "";

  if (lojas.length == 0) {
    lista.appendChild(criar("p", "vazio", "Nenhuma loja cadastrada por aqui ainda."));
    return;
  }

  lojas.forEach(function (l) {
    const card = criar("div", "card");
    const titulo = criar("h4", "clicavel", l.nome);
    titulo.addEventListener("click", function () {
      abrirNoMapa(l);
      pegarId("mapa").scrollIntoView({ behavior: "smooth", block: "nearest" });
    });
    card.appendChild(titulo);
    card.appendChild(criar("p", "detalhe", l.segmento + " · ★ " + notaFormatada(l.nota) + " (" + l.total_avaliacoes + ")"));
    card.appendChild(criar("p", "detalhe", l.endereco));
    card.appendChild(criar("p", "", l.descricao));
    const hoje = horarioHoje(l.horarios);
    if (hoje) card.appendChild(criar("p", "detalhe", hoje));

    l.itens.forEach(function (item) {
      const linha = criar("div", "item-vitrine");
      if (item.foto) {
        const img = document.createElement("img");
        img.src = item.foto;
        img.alt = item.nome;
        linha.appendChild(img);
      }
      linha.appendChild(criar("span", "", item.nome));
      linha.appendChild(criar("strong", "", dinheiro(item.valor)));
      if (usuario && usuario.perfil == "CLIENTE") {
        const reservar = criar("button", "mini-botao", "Reservar");
        reservar.type = "button";
        reservar.addEventListener("click", async function () {
          try {
            await api("POST", "/api/lojas/" + l.id + "/pedidos", { id_item: item.id });
            mostrarMensagem(msg, "Reservado: " + item.nome + ". Retire na loja.", "ok");
            mostrarPedidos();
          } catch (erro) {
            mostrarMensagem(msg, erro.erro, "erro");
          }
        });
        linha.appendChild(reservar);
      }
      card.appendChild(linha);
    });

    const acoes = criar("div", "acoes");
    const rota = criar("a", "mini-botao", "Como chegar");
    rota.href = linkRota(l.latitude, l.longitude);
    rota.target = "_blank";
    rota.rel = "noopener";
    acoes.appendChild(rota);
    if (l.whatsapp) {
      const zap = criar("a", "mini-botao", "WhatsApp");
      zap.href = "https://wa.me/55" + l.whatsapp;
      zap.target = "_blank";
      zap.rel = "noopener";
      acoes.appendChild(zap);
    }
    card.appendChild(acoes);

    if (usuario && usuario.perfil == "CLIENTE") card.appendChild(formularioAvaliar(l));
    lista.appendChild(card);
  });

  if (!usuario) {
    lista.appendChild(criar("p", "detalhe", "Entre como usuário para avaliar e reservar itens."));
  }
}

// ---------- eventos ----------
async function mostrarEventos() {
  const dados = await api("GET", "/api/eventos");
  const lista = pegarId("lista-eventos");
  lista.innerHTML = "";
  if (dados.eventos.length == 0) {
    lista.appendChild(criar("p", "vazio", "Nenhum evento anunciado."));
    return;
  }
  dados.eventos.forEach(function (ev) {
    const card = criar("div", "card");
    card.appendChild(criar("h4", "", ev.nome));
    card.appendChild(criar("p", "detalhe", ev.dia + " às " + ev.horario + " · " + ev.loja));
    if (ev.descricao) card.appendChild(criar("p", "", ev.descricao));
    if (ev.latitude !== null) {
      const rota = criar("a", "mini-botao", "Como chegar");
      rota.href = linkRota(ev.latitude, ev.longitude);
      rota.target = "_blank";
      rota.rel = "noopener";
      card.appendChild(rota);
    }
    lista.appendChild(card);
  });
}

// ---------- minhas reservas (só usuário) ----------
async function mostrarPedidos() {
  if (!(usuario && usuario.perfil == "CLIENTE")) return;
  const dados = await api("GET", "/api/meus-pedidos");
  const lista = pegarId("lista-pedidos");
  lista.innerHTML = "";
  if (dados.pedidos.length == 0) {
    lista.appendChild(criar("p", "vazio", "Você ainda não reservou nada."));
    return;
  }
  dados.pedidos.forEach(function (p) {
    const linha = criar("div", "pedido");
    const info = criar("div");
    info.appendChild(criar("strong", "", p.item));
    info.appendChild(criar("small", "", p.loja + " · " + dataBR(p.data)));
    linha.appendChild(info);
    linha.appendChild(criar("span", "", dinheiro(p.valor)));
    lista.appendChild(linha);
  });
}

// ---------- início ----------
pegarId("busca").addEventListener("input", carregarLojas);

(async function () {
  try {
    usuario = await quemSou();
    mostrarConta();
    await mostrarChips();
    await carregarLojas();
    mostrarEventos();
    mostrarPedidos();
  } catch (erro) {
    mostrarMensagem(msg, erro.erro || "Erro ao carregar.", "erro");
  }

  // o mapa carrega por último: se faltar a chave, a lista continua funcionando
  criarMapa(pegarId("mapa"), CARUARU, 14).then(
    function (m) {
      mapa = m;
      desenharMarcadores(lojas);
    },
    function () {}
  );
})();
