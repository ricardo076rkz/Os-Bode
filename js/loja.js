// Minha loja - Nordestinando

// ---------- dados de exemplo (depois vem do banco) ----------
const avaliacoes = [
  { cliente: "Maria S.", nota: 5, comentario: "Pastel crocante e atendimento excelente!", data: "2026-10-28" },
  { cliente: "João P.", nota: 4, comentario: "Muito bom, só demorou um pouco no sábado.", data: "2026-10-30" },
  { cliente: "Ana L.", nota: 5, comentario: "Recomendo, voltarei mais vezes.", data: "2026-11-02" },
  { cliente: "Carlos M.", nota: 3, comentario: "Bom sabor, mas o caldo de cana estava morno.", data: "2026-11-03" },
  { cliente: "Beatriz R.", nota: 5, comentario: "Preço justo e porção generosa.", data: "2026-11-05" }
];

const pedidos = [
  { item: "Pastel de carne", valor: 8.5, criado_em: "2026-11-01" },
  { item: "Pastel de queijo", valor: 7, criado_em: "2026-11-02" },
  { item: "Caldo de cana", valor: 6, criado_em: "2026-11-03" },
  { item: "Pastel de carne", valor: 8.5, criado_em: "2026-11-04" },
  { item: "Pastel de queijo", valor: 7, criado_em: "2026-11-05" },
  { item: "Caldo de cana", valor: 6, criado_em: "2026-11-06" }
];

const diasVisitas = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];
const valoresVisitas = [12, 18, 15, 22, 30, 41, 27];

// vitrine e eventos ficam salvos no navegador (localStorage)
let vitrine = pegar("vitrineLoja", [
  { id: 1, nome: "Pastel de carne", valor: 8.5, foto: "../js/img/pastel-carne.jpg" },
  { id: 2, nome: "Pastel de queijo", valor: 7, foto: "../js/img/pastel-queijo.jpg" },
  { id: 3, nome: "Caldo de cana", valor: 6, foto: "../js/img/caldo-de-cana.jpg" }
]);
let eventos = pegar("eventosLoja", []);

// ---------- funções pequenas ----------
function pegar(chave, padrao) {
  const texto = localStorage.getItem(chave);
  if (texto) {
    return JSON.parse(texto);
  }
  return padrao;
}

function guardar(chave, dados) {
  try {
    localStorage.setItem(chave, JSON.stringify(dados));
  } catch (erro) {
    alert("Não deu para salvar. Tente uma foto menor.");
  }
}

function pegarId(id) {
  return document.getElementById(id);
}

function criar(tag, classe, texto) {
  const elemento = document.createElement(tag);
  if (classe) elemento.className = classe;
  if (texto !== undefined) elemento.textContent = texto;
  return elemento;
}

function dinheiro(valor) {
  return "R$ " + valor.toFixed(2).replace(".", ",");
}

function dataBR(texto) {
  const partes = texto.split("-");
  return partes[2] + "/" + partes[1] + "/" + partes[0];
}

function estrelas(nota) {
  return "★".repeat(nota) + "☆".repeat(5 - nota);
}

function mediaNotas() {
  let soma = 0;
  avaliacoes.forEach(function (a) {
    soma += a.nota;
  });
  return soma / avaliacoes.length;
}

// diminui a foto antes de guardar, senão enche o localStorage
function reduzirFoto(arquivo, depois) {
  if (!arquivo) {
    depois("");
    return;
  }
  const leitor = new FileReader();
  leitor.onload = function () {
    const img = new Image();
    img.onload = function () {
      const escala = Math.min(1, 500 / img.width);
      const canvas = document.createElement("canvas");
      canvas.width = img.width * escala;
      canvas.height = img.height * escala;
      canvas.getContext("2d").drawImage(img, 0, 0, canvas.width, canvas.height);
      depois(canvas.toDataURL("image/jpeg", 0.7));
    };
    img.onerror = function () {
      depois("");
    };
    img.src = leitor.result;
  };
  leitor.readAsDataURL(arquivo);
}

// ---------- trocar de seção ----------
function abrirSecao(id) {
  document.querySelectorAll(".secao").forEach(function (s) {
    s.classList.add("oculto");
  });
  pegarId(id).classList.remove("oculto");
  window.scrollTo(0, 0);

  // marca o botão do menu de baixo que está ativo
  document.querySelectorAll(".menu-baixo button").forEach(function (b) {
    b.classList.toggle("ativo", b.dataset.abrir == id);
  });

  if (id == "inicio") mostrarResumo();
  if (id == "vitrine") mostrarVitrine();
  if (id == "evento") mostrarEventos();
  if (id == "avaliacoes") mostrarAvaliacoes();
  if (id == "estatisticas") mostrarEstatisticas();
}

// qualquer botão com data-abrir troca de seção (menu de baixo, Gerenciar, Ver loja)
document.addEventListener("click", function (e) {
  const botao = e.target.closest("[data-abrir]");
  if (botao) {
    abrirSecao(botao.dataset.abrir);
  }
});

// ---------- início ----------
function mostrarResumo() {
  pegarId("r-nota").textContent = mediaNotas().toFixed(1).replace(".", ",");
  pegarId("r-aval").textContent = avaliacoes.length;
  pegarId("r-itens").textContent = vitrine.length;
  pegarId("r-eventos").textContent = eventos.length;
}

// ---------- vitrine ----------
function mostrarVitrine() {
  const lista = pegarId("lista-vitrine");
  lista.innerHTML = "";

  if (vitrine.length == 0) {
    lista.appendChild(criar("p", "vazio", "Nenhum item na vitrine."));
    return;
  }

  vitrine.forEach(function (item) {
    const card = criar("div", "produto");

    // se a foto não carregar, mostra a primeira letra do nome
    const foto = criar("div", "produto-foto");
    if (item.foto) {
      const img = document.createElement("img");
      img.src = item.foto;
      img.alt = item.nome;
      img.onerror = function () {
        img.remove();
        foto.textContent = item.nome.charAt(0).toUpperCase();
      };
      foto.appendChild(img);
    } else {
      foto.textContent = item.nome.charAt(0).toUpperCase();
    }

    const remover = criar("button", "remover", "Remover");
    remover.type = "button";
    remover.addEventListener("click", function () {
      vitrine = vitrine.filter(function (v) {
        return v.id != item.id;
      });
      guardar("vitrineLoja", vitrine);
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
  const nome = pegarId("v-nome").value.trim();
  const valor = parseFloat(pegarId("v-valor").value);
  if (nome == "" || isNaN(valor)) return;

  reduzirFoto(pegarId("v-foto").files[0], function (foto) {
    vitrine.push({ id: Date.now(), nome: nome, valor: valor, foto: foto });
    guardar("vitrineLoja", vitrine);
    pegarId("form-vitrine").reset();
    mostrarVitrine();
  });
});

// ---------- anunciar evento ----------
function mostrarEventos() {
  const lista = pegarId("lista-eventos");
  lista.innerHTML = "";

  if (eventos.length == 0) {
    lista.appendChild(criar("p", "vazio", "Nenhum evento anunciado."));
    return;
  }

  eventos.forEach(function (ev) {
    const card = criar("div", "evento");
    card.appendChild(criar("h4", "", ev.nome));
    card.appendChild(criar("p", "", ev.dia + " às " + ev.horario));
    if (ev.descricao) card.appendChild(criar("p", "", ev.descricao));
    if (ev.latitude && ev.longitude) {
      card.appendChild(criar("p", "local", "Local: " + ev.latitude + ", " + ev.longitude));
    }

    const remover = criar("button", "remover", "Remover");
    remover.type = "button";
    remover.addEventListener("click", function () {
      eventos = eventos.filter(function (x) {
        return x.id != ev.id;
      });
      guardar("eventosLoja", eventos);
      mostrarEventos();
    });

    card.appendChild(remover);
    lista.appendChild(card);
  });
}

pegarId("form-evento").addEventListener("submit", function (e) {
  e.preventDefault();
  eventos.push({
    id: Date.now(),
    nome: pegarId("ev-nome").value.trim(),
    dia: pegarId("ev-dia").value,
    horario: pegarId("ev-hora").value,
    descricao: pegarId("ev-desc").value.trim(),
    latitude: pegarId("ev-lat").value,
    longitude: pegarId("ev-lng").value
  });
  guardar("eventosLoja", eventos);
  pegarId("form-evento").reset();
  mostrarEventos();
});

pegarId("btn-local").addEventListener("click", function () {
  if (!navigator.geolocation) {
    alert("Seu navegador não tem localização.");
    return;
  }
  navigator.geolocation.getCurrentPosition(
    function (pos) {
      pegarId("ev-lat").value = pos.coords.latitude.toFixed(6);
      pegarId("ev-lng").value = pos.coords.longitude.toFixed(6);
    },
    function () {
      alert("Não foi possível pegar a localização.");
    }
  );
});

// ---------- avaliações ----------
function mostrarAvaliacoes() {
  const media = mediaNotas();
  pegarId("nota-media").textContent = media.toFixed(1).replace(".", ",");
  pegarId("estrelas-media").textContent = estrelas(Math.round(media));
  pegarId("total-aval").textContent = avaliacoes.length + " avaliações";
  mostrarListaAvaliacoes();
}

function mostrarListaAvaliacoes() {
  const filtro = pegarId("filtro-nota").value;
  const lista = pegarId("lista-aval");
  lista.innerHTML = "";

  const filtradas = avaliacoes.filter(function (a) {
    return filtro == "todas" || a.nota == filtro;
  });

  if (filtradas.length == 0) {
    lista.appendChild(criar("p", "vazio", "Nenhuma avaliação com essa nota."));
    return;
  }

  filtradas.forEach(function (a) {
    const card = criar("div", "aval");
    const topo = criar("div", "aval-topo");
    topo.appendChild(criar("strong", "", a.cliente));
    topo.appendChild(criar("span", "estrelas", estrelas(a.nota)));
    card.appendChild(topo);
    card.appendChild(criar("p", "", a.comentario));
    card.appendChild(criar("small", "", dataBR(a.data)));
    lista.appendChild(card);
  });
}

pegarId("filtro-nota").addEventListener("change", mostrarListaAvaliacoes);

// ---------- estatísticas ----------
function mostrarEstatisticas() {
  let total = 0;
  pedidos.forEach(function (p) {
    total += p.valor;
  });

  pegarId("k-total").textContent = dinheiro(total);
  pegarId("k-pedidos").textContent = pedidos.length;
  pegarId("k-ticket").textContent = dinheiro(total / pedidos.length);
  pegarId("k-nota").textContent = mediaNotas().toFixed(1).replace(".", ",");

  // gráfico de visitas (as barras crescem com a transição do css)
  const grafico = pegarId("grafico");
  grafico.innerHTML = "";
  const maior = Math.max(...valoresVisitas);

  valoresVisitas.forEach(function (valor, i) {
    const coluna = criar("div", "coluna");
    const barra = criar("div", "barra");
    barra.style.height = "0px";
    coluna.appendChild(criar("span", "", valor));
    coluna.appendChild(barra);
    coluna.appendChild(criar("span", "", diasVisitas[i]));
    grafico.appendChild(coluna);

    setTimeout(function () {
      barra.style.height = (valor / maior) * 140 + "px";
    }, 50);
  });

  const lista = pegarId("lista-pedidos");
  lista.innerHTML = "";
  pedidos.forEach(function (p) {
    const linha = criar("div", "pedido");
    const info = criar("div");
    info.appendChild(criar("strong", "", p.item));
    info.appendChild(criar("small", "", dataBR(p.criado_em)));
    linha.appendChild(info);
    linha.appendChild(criar("span", "", dinheiro(p.valor)));
    lista.appendChild(linha);
  });
}

mostrarResumo();