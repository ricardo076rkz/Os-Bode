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
    montarAcoesTopo(area, usuario);
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
  const caixa = criar("div", "avaliar");
  const abrir = criar("button", "botao", "Avaliar e ganhar pontos");
  abrir.type = "button";
  abrir.addEventListener("click", function () {
    abrirAvaliacao(l, function () {
      carregarLojas();
      mostrarConta();
    });
  });
  caixa.appendChild(abrir);
  return caixa;
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

// ---------- agenda de eventos (cidade + lojas) ----------
const DIAS_LONGOS = { Segunda: "Segunda-feira", "Terça": "Terça-feira", Quarta: "Quarta-feira", Quinta: "Quinta-feira", Sexta: "Sexta-feira", "Sábado": "Sábado", Domingo: "Domingo" };
const NOMES_DIA = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"];
let agenda = [];
let filtroCategoria = "Todos";
let filtroDia = "Todos";
let marcadorEvento = null;

function hojeNome() {
  return NOMES_DIA[(new Date().getDay() + 6) % 7];
}

function textoQuando(ev) {
  return ev.dia + " · " + ev.periodo_rotulo + " · " + (ev.horario ? ev.horario : "horário a confirmar");
}

// mostra o local do evento no mapa (usa as coordenadas, ou procura o endereço pelo OpenStreetMap)
async function verEventoNoMapa(ev) {
  let ponto = null;
  if (ev.latitude !== null && ev.longitude !== null) ponto = { lat: ev.latitude, lng: ev.longitude };
  else if (ev.busca_mapa) {
    try { ponto = await buscarEndereco(ev.busca_mapa); } catch (e) { ponto = null; }
  }
  pegarId("mapa").scrollIntoView({ behavior: "smooth", block: "center" });
  if (ponto && mapa) {
    if (marcadorEvento) marcadorEvento.remove();
    marcadorEvento = L.marker([ponto.lat, ponto.lng], { title: ev.titulo }).addTo(mapa)
      .bindPopup(conteudoEvento(ev));
    mapa.setView([ponto.lat, ponto.lng], 17);
    marcadorEvento.openPopup();
    return;
  }
  // sem mapa carregado ou sem resultado: abre a busca no OpenStreetMap
  const consulta = ev.busca_mapa || (ev.local + ", Caruaru, PE");
  window.open("https://www.openstreetmap.org/search?query=" + encodeURIComponent(consulta), "_blank", "noopener");
  mostrarMensagem(msg, "Abri a busca do local em outra aba.", "info");
}

function conteudoEvento(ev) {
  const caixa = document.createElement("div");
  caixa.className = "balao";
  caixa.appendChild(criar("strong", "", ev.titulo));
  caixa.appendChild(document.createElement("br"));
  caixa.appendChild(document.createTextNode(ev.local));
  return caixa;
}

function cartaoEvento(ev) {
  const card = criar("article", "card evento-card2");

  const faixa = criar("div", "evento-faixa periodo-" + ev.periodo);
  faixa.appendChild(icone(ev.periodo == "manha" ? "sol" : ev.periodo == "tarde" ? "nuvem" : "estrela"));
  faixa.appendChild(criar("span", "", ev.foto ? "" : "Foto em breve"));
  if (ev.foto) {
    const img = document.createElement("img");
    img.src = ev.foto;
    img.alt = ev.titulo;
    img.loading = "lazy";
    faixa.innerHTML = "";
    faixa.appendChild(img);
  }
  card.appendChild(faixa);

  const corpo = criar("div", "evento-corpo");
  const marcas = criar("div", "linha-selos");
  marcas.appendChild(criar("span", "selo-categoria", ev.categoria));
  corpo.appendChild(marcas);
  corpo.appendChild(criar("h4", "", ev.titulo));
  corpo.appendChild(criar("p", "detalhe", textoQuando(ev)));
  const onde = criar("p", "detalhe local-linha");
  onde.appendChild(icone("pino"));
  onde.appendChild(document.createTextNode(ev.local));
  corpo.appendChild(onde);
  if (ev.descricao) corpo.appendChild(criar("p", "descricao-evento", ev.descricao));
  if (ev.pendencias.length) corpo.appendChild(criar("p", "pendente", "Algumas informações ainda serão validadas"));

  const acoes = criar("div", "acoes");
  const detalhes = criar("button", "mini-botao cheio", "Ver detalhes");
  detalhes.type = "button";
  detalhes.addEventListener("click", function () { abrirDetalhes(ev); });
  acoes.appendChild(detalhes);
  const noMapa = criar("button", "mini-botao");
  noMapa.type = "button";
  noMapa.appendChild(icone("pino"));
  noMapa.appendChild(document.createTextNode("Ver no mapa"));
  noMapa.addEventListener("click", function () { verEventoNoMapa(ev); });
  acoes.appendChild(noMapa);
  corpo.appendChild(acoes);
  card.appendChild(corpo);
  return card;
}

function abrirDetalhes(ev) {
  const d = pegarId("detalhe-evento");
  d.innerHTML = "";
  const topo = criar("div", "detalhe-topo");
  const titulo = criar("h2", "", ev.titulo);
  titulo.id = "detalhe-titulo";
  topo.appendChild(titulo);
  const fechar = criar("button", "icone-botao");
  fechar.type = "button";
  fechar.setAttribute("aria-label", "Fechar");
  fechar.textContent = "×";
  fechar.addEventListener("click", function () { d.close(); });
  topo.appendChild(fechar);
  d.appendChild(topo);

  const marcas = criar("div", "linha-selos");
  marcas.appendChild(criar("span", "selo-periodo periodo-" + ev.periodo, ev.periodo_rotulo));
  marcas.appendChild(criar("span", "selo-categoria", ev.categoria));
  d.appendChild(marcas);

  if (ev.descricao) d.appendChild(criar("p", "descricao-evento", ev.descricao));

  const quando = criar("div", "dado-linha");
  quando.appendChild(criar("span", "", "Quando"));
  quando.appendChild(criar("span", "", ev.dia + ", " + ev.periodo_rotulo.toLowerCase() + (ev.horario ? " · " + ev.horario : " · horário a confirmar")));
  d.appendChild(quando);
  const onde = criar("div", "dado-linha");
  onde.appendChild(criar("span", "", "Onde"));
  onde.appendChild(criar("span", "", ev.local));
  d.appendChild(onde);

  if (ev.detalhes.length) {
    d.appendChild(criar("h3", "", "O que você encontra"));
    const lista = criar("ul", "lista-detalhes");
    ev.detalhes.forEach(function (t) { lista.appendChild(criar("li", "", t)); });
    d.appendChild(lista);
  }
  if (ev.pendencias.length) {
    const caixa = criar("div", "caixa-pendente");
    caixa.appendChild(criar("strong", "", "Pendente de validação"));
    const lista = criar("ul", "lista-detalhes");
    ev.pendencias.forEach(function (t) { lista.appendChild(criar("li", "", t)); });
    caixa.appendChild(lista);
    d.appendChild(caixa);
  }

  const acoes = criar("div", "botoes-linha");
  const mapaBotao = criar("button", "botao", "Ver no mapa");
  mapaBotao.type = "button";
  mapaBotao.addEventListener("click", function () { d.close(); verEventoNoMapa(ev); });
  acoes.appendChild(mapaBotao);
  if (ev.id_loja) {
    const loja = criar("button", "botao contorno", "Ver a loja");
    loja.type = "button";
    loja.addEventListener("click", function () {
      d.close();
      pegarId("busca").value = ev.local;
      carregarLojas();
      pegarId("lista-lojas").scrollIntoView({ behavior: "smooth" });
    });
    acoes.appendChild(loja);
  }
  d.appendChild(acoes);
  d.showModal();
}

function desenharFiltrosEventos(dados) {
  const cat = pegarId("filtro-categoria");
  cat.innerHTML = "";
  ["Todos"].concat(dados.categorias).forEach(function (c) {
    const chip = criar("button", "chip" + (c == filtroCategoria ? " ativo" : ""), c);
    chip.type = "button";
    chip.addEventListener("click", function () { filtroCategoria = c; desenharFiltrosEventos(dados); desenharAgenda(); });
    cat.appendChild(chip);
  });
  const dia = pegarId("filtro-dia");
  dia.innerHTML = "";
  const diasComEvento = dados.dias.filter(function (d) { return dados.eventos.some(function (e) { return e.dia == d; }); });
  ["Todos", "Hoje"].concat(diasComEvento).forEach(function (d) {
    const chip = criar("button", "chip" + (d == filtroDia ? " ativo" : ""), d);
    chip.type = "button";
    chip.addEventListener("click", function () { filtroDia = d; desenharFiltrosEventos(dados); desenharAgenda(); });
    dia.appendChild(chip);
  });
}

function desenharAgenda() {
  const lista = pegarId("lista-eventos");
  lista.innerHTML = "";
  const hoje = hojeNome();
  const filtrados = agenda.filter(function (e) {
    if (filtroCategoria != "Todos" && e.categoria != filtroCategoria) return false;
    if (filtroDia == "Hoje") return e.dia == hoje;
    if (filtroDia != "Todos") return e.dia == filtroDia;
    return true;
  });
  if (!filtrados.length) {
    lista.appendChild(criar("p", "vazio", filtroDia == "Hoje" ? "Nenhum evento na agenda para hoje. Veja os outros dias." : "Nenhum evento com esses filtros."));
    return;
  }
  // um bloco por dia; dentro dele, manhã, tarde e noite separados
  const porDia = {};
  filtrados.forEach(function (e) { (porDia[e.dia] = porDia[e.dia] || []).push(e); });
  Object.keys(porDia).forEach(function (dia) {
    const bloco = criar("div", "agenda-dia");
    const cab = criar("h4", "agenda-dia-titulo", DIAS_LONGOS[dia] || dia);
    if (dia == hoje) cab.appendChild(criar("span", "selo-hoje", "hoje"));
    bloco.appendChild(cab);
    ["manha", "tarde", "noite"].forEach(function (periodo) {
      const doPeriodo = porDia[dia].filter(function (e) { return e.periodo == periodo; });
      if (!doPeriodo.length) return;
      const secao = criar("div", "agenda-periodo");
      secao.appendChild(criar("p", "agenda-periodo-nome periodo-" + periodo, doPeriodo[0].periodo_rotulo));
      const grade = criar("div", "agenda-grade2");
      doPeriodo.forEach(function (e) { grade.appendChild(cartaoEvento(e)); });
      secao.appendChild(grade);
      bloco.appendChild(secao);
    });
    lista.appendChild(bloco);
  });
}

async function mostrarEventos() {
  const lista = pegarId("lista-eventos");
  lista.innerHTML = "";
  lista.appendChild(criar("div", "esqueleto alto"));
  try {
    const dados = await api("GET", "/api/agenda");
    agenda = dados.eventos;
    if (!agenda.length) {
      lista.innerHTML = "";
      lista.appendChild(criar("p", "vazio", "Nenhum evento na agenda por enquanto."));
      return;
    }
    desenharFiltrosEventos(dados);
    desenharAgenda();
  } catch (erro) {
    lista.innerHTML = "";
    lista.appendChild(criar("p", "vazio", "Não consegui carregar a agenda agora."));
  }
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
