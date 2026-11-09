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

function montarCapa(l) {
  const capa = criar("div", "capa");
  if (l.foto) {
    const img = document.createElement("img");
    img.className = "capa-foto";
    img.src = l.foto;
    img.alt = "";
    capa.appendChild(img);
  } else {
    capa.appendChild(criar("div", "capa-inicial", inicial(l.nome)));
  }
  if (l.logo) {
    const logo = document.createElement("img");
    logo.className = "avatar";
    logo.src = l.logo;
    logo.alt = "";
    capa.appendChild(logo);
  } else {
    capa.appendChild(criar("div", "avatar", inicial(l.nome)));
  }
  return capa;
}

function mostrarLojas() {
  const lista = pegarId("lista-lojas");
  lista.innerHTML = "";

  if (lojas.length == 0) {
    lista.appendChild(criar("p", "vazio", "Nenhuma loja encontrada. Quando um comerciante se cadastrar, ela aparece aqui."));
    return;
  }

  lojas.forEach(function (l) {
    const card = criar("div", "card com-avatar");
    card.appendChild(montarCapa(l));

    const corpo = criar("div", "card-corpo");

    const cabeca = criar("div", "cabeca-loja");
    const nomes = criar("div");
    const titulo = criar("h4", "clicavel", l.nome);
    titulo.addEventListener("click", function () {
      abrirNoMapa(l);
      pegarId("mapa").scrollIntoView({ behavior: "smooth", block: "nearest" });
    });
    nomes.appendChild(titulo);
    nomes.appendChild(criar("p", "detalhe", l.segmento));
    cabeca.appendChild(nomes);

    const nota = criar("span", "nota");
    nota.appendChild(icone("estrela"));
    nota.appendChild(document.createTextNode(l.nota === null ? "Novo" : notaFormatada(l.nota) + " (" + l.total_avaliacoes + ")"));
    cabeca.appendChild(nota);
    corpo.appendChild(cabeca);

    corpo.appendChild(criar("p", "", l.descricao));

    const selos = criar("div", "selos");
    const status = abertoAgora(l.horarios);
    if (status) selos.appendChild(criar("span", "selo " + (status.aberto ? "aberto" : "fechado"), status.texto));
    selos.appendChild(criar("span", "selo", l.endereco));
    corpo.appendChild(selos);

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
      corpo.appendChild(linha);
    });

    const acoes = criar("div", "acoes");
    const rota = criar("a", "mini-botao", "Como chegar");
    rota.prepend(icone("rota"));
    rota.href = linkRota(l.latitude, l.longitude);
    rota.target = "_blank";
    rota.rel = "noopener";
    acoes.appendChild(rota);
    if (l.whatsapp) {
      const zap = criar("a", "mini-botao", "WhatsApp");
      zap.prepend(icone("conversa"));
      zap.href = "https://wa.me/55" + l.whatsapp;
      zap.target = "_blank";
      zap.rel = "noopener";
      acoes.appendChild(zap);
    }
    if (l.telefone) {
      const ligar = criar("a", "mini-botao", "Ligar");
      ligar.prepend(icone("telefone"));
      ligar.href = "tel:" + l.telefone;
      acoes.appendChild(ligar);
    }
    corpo.appendChild(acoes);

    if (usuario && usuario.perfil == "CLIENTE") corpo.appendChild(formularioAvaliar(l));
    card.appendChild(corpo);
    lista.appendChild(card);
  });

  if (!usuario) {
    lista.appendChild(criar("p", "vazio", "Entre como usuário para avaliar lojas e reservar itens."));
  }
}

// ---------- eventos ----------
async function mostrarEventos() {
  const dados = await api("GET", "/api/eventos");
  const lista = pegarId("lista-eventos");
  lista.innerHTML = "";
  if (dados.eventos.length == 0) {
    lista.appendChild(criar("p", "vazio", "Nenhum evento anunciado por enquanto."));
    return;
  }
  dados.eventos.forEach(function (ev) {
    const card = criar("div", "card evento-card");

    const dia = criar("div", "evento-dia");
    dia.appendChild(criar("strong", "", ev.dia.slice(0, 3)));
    dia.appendChild(criar("small", "", ev.horario));
    card.appendChild(dia);

    const texto = criar("div");
    texto.appendChild(criar("h4", "", ev.nome));
    texto.appendChild(criar("p", "detalhe", ev.dia + " às " + ev.horario + " · " + ev.loja));
    if (ev.descricao) texto.appendChild(criar("p", "", ev.descricao));
    if (ev.latitude !== null) {
      const acoes = criar("div", "acoes");
      const rota = criar("a", "mini-botao", "Como chegar");
      rota.prepend(icone("rota"));
      rota.href = linkRota(ev.latitude, ev.longitude);
      rota.target = "_blank";
      rota.rel = "noopener";
      acoes.appendChild(rota);
      texto.appendChild(acoes);
    }
    card.appendChild(texto);
    lista.appendChild(card);
  });
}

// ---------- clima de Caruaru (Open-Meteo: gratuito, sem chave) ----------
const CLIMA = [
  [[0], "Céu limpo", "sol"],
  [[1, 2], "Poucas nuvens", "sol"],
  [[3, 45, 48], "Nublado", "nuvem"],
  [[51, 53, 55, 56, 57], "Garoa", "chuva"],
  [[61, 63, 65, 66, 67, 80, 81, 82], "Chuva", "chuva"],
  [[95, 96, 99], "Trovoadas", "chuva"]
];

async function mostrarClima() {
  const area = pegarId("clima");
  try {
    const url = "https://api.open-meteo.com/v1/forecast?latitude=" + CARUARU.lat + "&longitude=" + CARUARU.lng +
      "&current=temperature_2m,weather_code&timezone=America%2FSao_Paulo";
    const resposta = await fetch(url);
    if (!resposta.ok) throw new Error("clima");
    const dados = await resposta.json();
    const temperatura = Math.round(dados.current.temperature_2m);
    const codigo = dados.current.weather_code;
    const achou = CLIMA.find(function (c) {
      return c[0].indexOf(codigo) != -1;
    }) || [[], "Tempo variável", "nuvem"];

    area.innerHTML = "";
    area.appendChild(icone(achou[2]));
    area.appendChild(document.createTextNode(temperatura + "°C agora em Caruaru · " + achou[1]));
    area.classList.remove("oculto");
  } catch (erro) {
    // sem clima não atrapalha nada: o aviso simplesmente não aparece
    area.classList.add("oculto");
  }
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
    mostrarClima();
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
