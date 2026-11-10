// Minha loja - painel do comerciante (depende de comum.js, api.js e mapa.js)
// Tudo aqui vem do servidor; nada é de exemplo.

let loja = null;
let localizacao = null;
let novoLogo; // undefined = não mexeu
let novaFoto;

// ---------- entrar / sair ----------
function voltarAoLogin() {
  window.location.href = "comerciante.html";
}

pegarId("sair").addEventListener("click", async function (e) {
  e.preventDefault();
  try {
    await api("POST", "/api/logout");
  } catch (erro) {}
  voltarAoLogin();
});

async function carregarLoja() {
  try {
    const dados = await api("GET", "/api/minha-loja");
    loja = dados.loja;
  } catch (erro) {
    // sem login, ou conta de usuário: não é área dele
    voltarAoLogin();
    throw erro;
  }
  pegarId("loja-nome").textContent = loja.nome;
  pegarId("loja-endereco").textContent = loja.endereco;
  desenharCapa();
}

// foto de capa e logotipo da loja (ou a inicial, se ainda não enviou)
function desenharCapa() {
  const capa = pegarId("loja-capa");
  capa.innerHTML = "";
  if (loja.foto) {
    const img = document.createElement("img");
    img.className = "capa-foto";
    img.src = loja.foto;
    img.alt = "";
    capa.appendChild(img);
  } else {
    capa.appendChild(criar("div", "capa-inicial", inicial(loja.nome)));
  }
  if (loja.logo) {
    const logo = document.createElement("img");
    logo.className = "avatar";
    logo.src = loja.logo;
    logo.alt = "";
    capa.appendChild(logo);
  } else {
    capa.appendChild(criar("div", "avatar", inicial(loja.nome)));
  }
}

// ---------- trocar de seção ----------
function abrirSecao(id) {
  document.querySelectorAll(".secao").forEach(function (s) {
    s.classList.add("oculto");
  });
  pegarId(id).classList.remove("oculto");
  document.querySelector(".tela").scrollTop = 0;

  document.querySelectorAll(".menu-baixo button").forEach(function (b) {
    b.classList.toggle("ativo", b.dataset.abrir == id);
  });

  if (id == "inicio") mostrarResumo();
  if (id == "vitrine") mostrarVitrine();
  if (id == "evento") mostrarEventos();
  if (id == "avaliacoes") mostrarAvaliacoes();
  if (id == "estatisticas") mostrarEstatisticas();
  if (id == "dados") mostrarDados();
  if (id == "promocoes") mostrarPromocoes();
  if (id == "validar") mostrarVouchers();
}

document.addEventListener("click", function (e) {
  const botao = e.target.closest("[data-abrir]");
  if (botao) abrirSecao(botao.dataset.abrir);
});

// ---------- início ----------
async function mostrarResumo() {
  try {
    await carregarLoja();
    if (!pegarId("acoes-topo").firstChild) montarAcoesTopo(pegarId("acoes-topo"), { nome: loja.responsavel });
    const s = await api("GET", "/api/minha-loja/estatisticas");
    pegarId("r-nota").textContent = notaFormatada(s.nota_media);
    pegarId("r-aval").textContent = s.total_avaliacoes;
    pegarId("r-itens").textContent = s.itens;
    pegarId("r-eventos").textContent = s.eventos;
  } catch (erro) {}
}

// ---------- vitrine ----------
async function mostrarVitrine() {
  await carregarLoja();
  const lista = pegarId("lista-vitrine");
  lista.innerHTML = "";

  if (loja.itens.length == 0) {
    lista.appendChild(criar("p", "vazio", "Nenhum item na vitrine ainda."));
    return;
  }

  loja.itens.forEach(function (item) {
    const card = criar("div", "produto");
    const foto = criar("div", "produto-foto");
    if (item.foto) {
      const img = document.createElement("img");
      img.src = item.foto;
      img.alt = item.nome;
      foto.appendChild(img);
    } else {
      foto.textContent = item.nome.charAt(0).toUpperCase();
    }

    const remover = criar("button", "remover", "Remover");
    remover.type = "button";
    remover.addEventListener("click", async function () {
      await api("DELETE", "/api/minha-loja/vitrine/" + item.id);
      mostrarVitrine();
    });

    card.appendChild(foto);
    card.appendChild(criar("h4", "", item.nome));
    card.appendChild(criar("p", "preco", dinheiro(item.valor)));
    card.appendChild(remover);
    lista.appendChild(card);
  });
}

pegarId("form-vitrine").addEventListener("submit", function (e) {
  e.preventDefault();
  const formulario = e.target;
  const aviso = pegarId("mensagem-vitrine");
  reduzirFoto(pegarId("v-foto").files[0], 500, async function (foto) {
    try {
      await api("POST", "/api/minha-loja/vitrine", {
        nome: pegarId("v-nome").value,
        valor: pegarId("v-valor").value,
        foto: foto
      });
      formulario.reset();
      mostrarErrosCampos(formulario, {});
      aviso.className = "mensagem oculto";
      mostrarVitrine();
    } catch (erro) {
      mostrarErrosCampos(formulario, erro.campos);
      mostrarMensagem(aviso, erro.erro, "erro");
    }
  });
});

// ---------- anunciar evento ----------
async function mostrarEventos() {
  await carregarLoja();
  const lista = pegarId("lista-eventos");
  lista.innerHTML = "";

  if (loja.eventos.length == 0) {
    lista.appendChild(criar("p", "vazio", "Nenhum evento anunciado."));
    return;
  }

  loja.eventos.forEach(function (ev) {
    const card = criar("div", "evento");
    card.appendChild(criar("h4", "", ev.nome));
    card.appendChild(criar("p", "evento-quando", ev.dia + " às " + ev.horario));
    if (ev.descricao) card.appendChild(criar("p", "", ev.descricao));
    if (ev.latitude !== null && ev.longitude !== null) {
      card.appendChild(criar("p", "local", "Local: " + ev.latitude + ", " + ev.longitude));
    } else {
      card.appendChild(criar("p", "local", "Local: o endereço da loja"));
    }

    const remover = criar("button", "remover", "Remover");
    remover.type = "button";
    remover.addEventListener("click", async function () {
      await api("DELETE", "/api/minha-loja/eventos/" + ev.id);
      mostrarEventos();
    });
    card.appendChild(remover);
    lista.appendChild(card);
  });
}

pegarId("form-evento").addEventListener("submit", async function (e) {
  e.preventDefault();
  const formulario = e.target;
  const aviso = pegarId("mensagem-evento");
  try {
    await api("POST", "/api/minha-loja/eventos", {
      nome: pegarId("ev-nome").value,
      dia: pegarId("ev-dia").value,
      horario: pegarId("ev-hora").value,
      descricao: pegarId("ev-desc").value,
      latitude: pegarId("ev-lat").value,
      longitude: pegarId("ev-lng").value
    });
    formulario.reset();
    mostrarErrosCampos(formulario, {});
    aviso.className = "mensagem oculto";
    mostrarEventos();
  } catch (erro) {
    mostrarErrosCampos(formulario, erro.campos);
    mostrarMensagem(aviso, erro.erro, "erro");
  }
});

pegarId("btn-local").addEventListener("click", function () {
  const aviso = pegarId("mensagem-evento");
  if (!navigator.geolocation) {
    mostrarMensagem(aviso, "Este aparelho não informa localização.", "erro");
    return;
  }
  navigator.geolocation.getCurrentPosition(
    function (pos) {
      pegarId("ev-lat").value = pos.coords.latitude.toFixed(6);
      pegarId("ev-lng").value = pos.coords.longitude.toFixed(6);
    },
    function () {
      mostrarMensagem(aviso, "Não foi possível pegar a localização. Deixe em branco para usar o endereço da loja.", "erro");
    }
  );
});

// ---------- avaliações ----------
let todasAvaliacoes = [];

async function mostrarAvaliacoes() {
  const dados = await api("GET", "/api/minha-loja/avaliacoes");
  todasAvaliacoes = dados.avaliacoes;

  let soma = 0;
  todasAvaliacoes.forEach(function (a) {
    soma += a.nota;
  });
  const media = todasAvaliacoes.length ? soma / todasAvaliacoes.length : null;

  pegarId("nota-media").textContent = notaFormatada(media);
  pegarId("estrelas-media").textContent = media === null ? "" : estrelas(Math.round(media));
  pegarId("total-aval").textContent = todasAvaliacoes.length + (todasAvaliacoes.length == 1 ? " avaliação" : " avaliações");
  mostrarListaAvaliacoes();
}

function mostrarListaAvaliacoes() {
  const filtro = pegarId("filtro-nota").value;
  const lista = pegarId("lista-aval");
  lista.innerHTML = "";

  const filtradas = todasAvaliacoes.filter(function (a) {
    return filtro == "todas" || a.nota == filtro;
  });

  if (filtradas.length == 0) {
    lista.appendChild(criar("p", "vazio", todasAvaliacoes.length ? "Nenhuma avaliação com essa nota." : "Ainda não há avaliações."));
    return;
  }

  filtradas.forEach(function (a) {
    const card = criar("div", "aval");
    const topo = criar("div", "aval-topo");
    topo.appendChild(criar("strong", "", a.cliente));
    topo.appendChild(criar("span", "estrelas", estrelas(a.nota)));
    card.appendChild(topo);
    if (a.comentario) card.appendChild(criar("p", "", a.comentario));
    card.appendChild(criar("small", "", dataBR(a.data)));
    lista.appendChild(card);
  });
}

pegarId("filtro-nota").addEventListener("change", mostrarListaAvaliacoes);

// ---------- estatísticas (tudo calculado no servidor a partir do banco) ----------
async function mostrarEstatisticas() {
  const s = await api("GET", "/api/minha-loja/estatisticas");

  pegarId("k-total").textContent = dinheiro(s.total_vendido);
  pegarId("k-pedidos").textContent = s.pedidos;
  pegarId("k-ticket").textContent = dinheiro(s.ticket_medio);
  pegarId("k-nota").textContent = notaFormatada(s.nota_media);

  const grafico = pegarId("grafico");
  grafico.innerHTML = "";
  const notas = ["1", "2", "3", "4", "5"];
  const maior = Math.max(1, ...notas.map(function (n) { return s.avaliacoes_por_nota[n]; }));

  notas.forEach(function (n) {
    const quantidade = s.avaliacoes_por_nota[n];
    const coluna = criar("div", "coluna");
    const barra = criar("div", "barra");
    barra.style.height = "0px";
    coluna.appendChild(criar("span", "", quantidade));
    coluna.appendChild(barra);
    coluna.appendChild(criar("span", "", n + "★"));
    grafico.appendChild(coluna);
    // a barra cresce com a transição do css
    setTimeout(function () {
      barra.style.height = (quantidade / maior) * 140 + "px";
    }, 50);
  });

  const lista = pegarId("lista-pedidos");
  lista.innerHTML = "";
  if (s.ultimos_pedidos.length == 0) {
    lista.appendChild(criar("p", "vazio", "Nenhuma reserva ainda."));
    return;
  }
  s.ultimos_pedidos.forEach(function (p) {
    const linha = criar("div", "pedido");
    const info = criar("div");
    info.appendChild(criar("strong", "", p.item));
    info.appendChild(criar("small", "", p.cliente + " · " + dataBR(p.data)));
    linha.appendChild(info);
    linha.appendChild(criar("span", "", dinheiro(p.valor)));
    lista.appendChild(linha);
  });
}

// ---------- dados e localização da loja ----------
const formDados = pegarId("form-dados");
mascaraTelefone(pegarId("telefone_comercial"));
mascaraTelefone(pegarId("whatsapp"));
mascaraCNPJ(pegarId("cnpj"));
mascaraCEP(pegarId("cep"));

pegarId("logo").addEventListener("change", function () {
  reduzirFoto(this.files[0], 300, function (d) { novoLogo = d; });
});
pegarId("foto").addEventListener("change", function () {
  reduzirFoto(this.files[0], 700, function (d) { novaFoto = d; });
});

async function mostrarDados() {
  await carregarLoja();
  const config = await api("GET", "/api/config");

  const select = pegarId("segmento");
  select.innerHTML = "";
  config.segmentos.forEach(function (seg) {
    const o = document.createElement("option");
    o.textContent = seg;
    select.appendChild(o);
  });

  const campos = ["nome_fantasia", "segmento", "descricao", "cnpj", "razao_social", "whatsapp", "instagram", "site", "cep", "rua", "numero", "bairro", "cidade", "estado", "latitude", "longitude"];
  const valores = {
    nome_fantasia: loja.nome, segmento: loja.segmento, descricao: loja.descricao, cnpj: loja.cnpj || "",
    razao_social: loja.razao_social || "", whatsapp: telefoneBR(loja.whatsapp), instagram: loja.instagram || "",
    site: loja.site || "", cep: loja.cep, rua: loja.rua, numero: loja.numero, bairro: loja.bairro,
    cidade: loja.cidade, estado: loja.estado, latitude: loja.latitude, longitude: loja.longitude
  };
  campos.forEach(function (c) {
    pegarId(c).value = valores[c];
  });
  pegarId("telefone_comercial").value = telefoneBR(loja.telefone);
  if (loja.cnpj) pegarId("cnpj").value = loja.cnpj.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, "$1.$2.$3/$4-$5");
  if (loja.cep) pegarId("cep").value = loja.cep.replace(/^(\d{5})(\d{3})$/, "$1-$2");
  montarHorarios(pegarId("horarios"), loja.horarios);

  // o mapa é criado uma vez, já com o ponto salvo
  if (!localizacao) {
    localizacao = iniciarLocalizacao({
      cep: pegarId("cep"), rua: pegarId("rua"), numero: pegarId("numero"), bairro: pegarId("bairro"),
      cidade: pegarId("cidade"), estado: pegarId("estado"),
      lat: pegarId("latitude"), lng: pegarId("longitude"),
      botao: pegarId("btn-localizar"), mapa: pegarId("mapa"), aviso: pegarId("aviso-mapa")
    });
  } else {
    localizacao.definir(loja.latitude, loja.longitude);
    localizacao.reajustar();
  }
}

formDados.addEventListener("submit", async function (e) {
  e.preventDefault();
  const aviso = pegarId("mensagem-dados");
  mostrarErrosCampos(formDados, {});

  const corpo = {
    nome_fantasia: pegarId("nome_fantasia").value, segmento: pegarId("segmento").value,
    descricao: pegarId("descricao").value, cnpj: pegarId("cnpj").value, razao_social: pegarId("razao_social").value,
    telefone_comercial: pegarId("telefone_comercial").value, whatsapp: pegarId("whatsapp").value,
    instagram: pegarId("instagram").value, site: pegarId("site").value,
    cep: pegarId("cep").value, rua: pegarId("rua").value, numero: pegarId("numero").value,
    bairro: pegarId("bairro").value, cidade: pegarId("cidade").value, estado: pegarId("estado").value,
    latitude: pegarId("latitude").value, longitude: pegarId("longitude").value,
    horarios: lerHorarios(pegarId("horarios"))
  };
  if (novoLogo !== undefined) corpo.logo = novoLogo;
  if (novaFoto !== undefined) corpo.foto = novaFoto;

  try {
    await api("PUT", "/api/minha-loja", corpo);
    novoLogo = novaFoto = undefined;
    await carregarLoja();
    mostrarMensagem(aviso, "Alterações salvas.", "ok");
  } catch (erro) {
    mostrarErrosCampos(formDados, erro.campos);
    mostrarMensagem(aviso, erro.campos.horarios || erro.erro, "erro");
  }
});

mostrarResumo();


// ---------- promoções e vouchers ----------
const ESTADOS_PROMO = { ativa: "Ativa", pausada: "Pausada", encerrada: "Encerrada" };

function limparErrosPromo() {
  document.querySelectorAll("#form-promocao .erro-campo").forEach(function (e) { e.remove(); });
}

pegarId("pr-tipo").addEventListener("change", function () {
  const t = this.value;
  pegarId("pr-valor-caixa").classList.toggle("oculto", t != "percentual" && t != "valor_fixo");
  pegarId("pr-valor-rotulo").textContent = t == "percentual" ? "Percentual (1 a 100)" : "Valor do desconto (R$)";
});

async function mostrarPromocoes() {
  const hoje = new Date().toISOString().slice(0, 10);
  if (!pegarId("pr-inicio").value) pegarId("pr-inicio").value = hoje;
  const lista = pegarId("lista-promocoes");
  try {
    const d = await api("GET", "/api/minha-loja/promocoes");
    lista.innerHTML = "";
    if (!d.promocoes.length) {
      const v = criar("div", "estado-vazio");
      v.appendChild(criar("strong", "", "Nenhuma promoção ainda"));
      v.appendChild(criar("span", "", "Crie a primeira acima para os clientes trocarem pontos por benefícios na sua loja."));
      lista.appendChild(v);
      return;
    }
    d.promocoes.forEach(function (p) {
      const el = criar("article", "cartao promo");
      el.appendChild(criar("strong", "", p.titulo + " · " + p.beneficio));
      el.appendChild(criar("p", "", p.pontos + " pontos · " + ESTADOS_PROMO[p.status] + " · até " + dataBR(p.validade)));
      el.appendChild(criar("p", "recompensa-meta", "Disponíveis " + (p.quantidade_total - p.resgatados) + " de " + p.quantidade_total + " · resgatados " + p.resgatados + " · utilizados " + p.utilizados + " · expirados " + p.expirados + " · cancelados " + p.cancelados));
      if (p.status != "encerrada") {
        const bt = criar("div", "botoes-linha");
        const alternar = criar("button", "botao contorno", p.status == "ativa" ? "Pausar" : "Ativar");
        alternar.type = "button";
        alternar.addEventListener("click", async function () {
          try { await api("PATCH", "/api/minha-loja/promocoes/" + p.id, { status: p.status == "ativa" ? "pausada" : "ativa" }); mostrarPromocoes(); } catch (e) { mostrarMensagem(pegarId("mensagem-promocao"), e.erro, "erro"); }
        });
        const encerrar = criar("button", "botao contorno", "Encerrar");
        encerrar.type = "button";
        encerrar.addEventListener("click", async function () {
          if (!confirm("Encerrar esta promoção? Vouchers já resgatados continuam valendo.")) return;
          try { await api("PATCH", "/api/minha-loja/promocoes/" + p.id, { status: "encerrada" }); mostrarPromocoes(); } catch (e) { mostrarMensagem(pegarId("mensagem-promocao"), e.erro, "erro"); }
        });
        bt.appendChild(alternar);
        bt.appendChild(encerrar);
        el.appendChild(bt);
      }
      lista.appendChild(el);
    });
  } catch (e) {}
}

pegarId("form-promocao").addEventListener("submit", async function (ev) {
  ev.preventDefault();
  limparErrosPromo();
  const ids = { titulo: "pr-titulo", descricao: "pr-descricao", tipo_beneficio: "pr-tipo", valor_beneficio: "pr-valor", pontos_necessarios: "pr-pontos", quantidade_total: "pr-qtd", limite_por_usuario: "pr-limite", inicio: "pr-inicio", fim: "pr-fim", condicoes: "pr-cond" };
  const corpo = {};
  Object.keys(ids).forEach(function (k) { corpo[k] = pegarId(ids[k]).value; });
  const msgP = pegarId("mensagem-promocao");
  try {
    await api("POST", "/api/minha-loja/promocoes", corpo);
    mostrarMensagem(msgP, "Promoção publicada.", "ok");
    ["pr-titulo", "pr-descricao", "pr-valor", "pr-pontos", "pr-qtd", "pr-fim", "pr-cond"].forEach(function (i) { pegarId(i).value = ""; });
    mostrarPromocoes();
  } catch (e) {
    mostrarMensagem(msgP, e.erro, "erro");
    Object.keys(e.campos || {}).forEach(function (k) {
      const campo = pegarId(ids[k]);
      if (campo) campo.insertAdjacentElement("afterend", criar("small", "erro-campo", e.campos[k]));
    });
  }
});

async function mostrarVouchers() {
  const lista = pegarId("lista-vouchers");
  try {
    const d = await api("GET", "/api/minha-loja/vouchers");
    lista.innerHTML = "";
    if (!d.vouchers.length) {
      const v = criar("div", "estado-vazio");
      v.appendChild(criar("strong", "", "Nenhum voucher resgatado ainda"));
      v.appendChild(criar("span", "", "Quando um cliente resgatar uma promoção, o voucher aparece aqui."));
      lista.appendChild(v);
      return;
    }
    d.vouchers.forEach(function (v) {
      const el = criar("div", "voucher-item estado-" + v.estado);
      const esq = criar("div", "");
      esq.appendChild(criar("strong", "", v.codigo));
      esq.appendChild(criar("small", "", v.titulo + " · " + v.cliente));
      el.appendChild(esq);
      el.appendChild(criar("span", "selo-estado", v.estado_rotulo));
      if (v.estado == "resgatado") {
        const c = criar("button", "mini-botao", "Cancelar");
        c.type = "button";
        c.addEventListener("click", async function () {
          if (!confirm("Cancelar este voucher? Os pontos voltam para o cliente.")) return;
          try { await api("POST", "/api/minha-loja/vouchers/" + v.id + "/cancelar"); mostrarVouchers(); } catch (e) { mostrarMensagem(pegarId("mensagem-voucher"), e.erro, "erro"); }
        });
        el.appendChild(c);
      }
      lista.appendChild(el);
    });
  } catch (e) {}
}

function mostrarResultadoVoucher(v, textoOk) {
  const r = pegarId("vc-resultado");
  r.innerHTML = "";
  const caixa = criar("div", "cartao estado-" + v.estado);
  caixa.appendChild(criar("strong", "", v.titulo));
  [["Benefício", v.beneficio], ["Cliente", v.cliente], ["Estado", v.estado_rotulo], ["Válido até", dataBR(v.validade)]].forEach(function (p) {
    const l = criar("div", "dado-linha");
    l.appendChild(criar("span", "", p[0]));
    l.appendChild(criar("span", "", p[1]));
    caixa.appendChild(l);
  });
  r.appendChild(caixa);
}

pegarId("vc-consultar").addEventListener("click", async function () {
  const m = pegarId("mensagem-voucher");
  pegarId("vc-resultado").innerHTML = "";
  try {
    const d = await api("GET", "/api/minha-loja/vouchers/consultar?codigo=" + encodeURIComponent(pegarId("vc-codigo").value));
    mostrarResultadoVoucher(d.voucher);
    m.classList.add("oculto");
  } catch (e) { mostrarMensagem(m, e.erro, "erro"); }
});

pegarId("form-validar").addEventListener("submit", async function (ev) {
  ev.preventDefault();
  const m = pegarId("mensagem-voucher");
  pegarId("vc-resultado").innerHTML = "";
  try {
    const d = await api("POST", "/api/minha-loja/vouchers/validar", { codigo: pegarId("vc-codigo").value });
    mostrarMensagem(m, "Voucher validado. Dê o benefício ao cliente.", "ok");
    mostrarResultadoVoucher(d.voucher);
    pegarId("vc-codigo").value = "";
    mostrarVouchers();
  } catch (e) { mostrarMensagem(m, e.erro, "erro"); }
});
