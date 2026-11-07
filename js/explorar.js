// Explorar cidade - Nordestinando
// Lojas e evento de exemplo (os mesmos do banco.sql) + a loja e os eventos
// que o comerciante cadastrou na tela Minha loja (ficam no localStorage)

const lojasExemplo = [
  { nome: "Café da Estação", segmento: "Cafeteria", nota: 4.9, itens: [] },
  { nome: "Artesanato Caruaru", segmento: "Souvenirs", nota: 4.7, itens: [] }
];

const eventosExemplo = [
  {
    nome: "Grande Motofest",
    dia: "Quinta-feira",
    horario: "19:00",
    descricao: "Encontro de motociclistas no Polo da Estação Ferroviária"
  }
];

// a loja do comerciante (Pastelaria) entra na lista com a vitrine dela
const lojas = lojasExemplo.concat([
  {
    nome: dadosLoja.nome,
    segmento: "Alimentação",
    nota: mediaNotas(),
    itens: pegar("vitrineLoja", vitrinePadrao)
  }
]);

const eventos = eventosExemplo.concat(pegar("eventosLoja", []));

let segmentoEscolhido = "Todos";

function mostrarChips() {
  const chips = pegarId("chips");
  chips.innerHTML = "";

  const segmentos = ["Todos"];
  lojas.forEach(function (l) {
    if (segmentos.indexOf(l.segmento) == -1) segmentos.push(l.segmento);
  });

  segmentos.forEach(function (seg) {
    const chip = criar("button", "chip", seg);
    chip.type = "button";
    if (seg == segmentoEscolhido) chip.classList.add("ativo");
    chip.addEventListener("click", function () {
      segmentoEscolhido = seg;
      mostrarChips();
      mostrarLojas();
    });
    chips.appendChild(chip);
  });
}

function mostrarLojas() {
  const lista = pegarId("lista-lojas");
  const busca = pegarId("busca").value.trim().toLowerCase();
  lista.innerHTML = "";

  const filtradas = lojas.filter(function (l) {
    const segmentoOk = segmentoEscolhido == "Todos" || l.segmento == segmentoEscolhido;
    const buscaOk = l.nome.toLowerCase().indexOf(busca) != -1;
    return segmentoOk && buscaOk;
  });

  if (filtradas.length == 0) {
    lista.appendChild(criar("p", "vazio", "Nenhuma loja encontrada."));
    return;
  }

  filtradas.forEach(function (l) {
    const card = criar("div", "card");
    card.appendChild(criar("h4", "", l.nome));
    card.appendChild(criar("p", "detalhe", l.segmento + " · ★ " + notaFormatada(l.nota)));

    l.itens.forEach(function (item) {
      const linha = criar("div", "item-vitrine");
      if (item.foto) {
        const img = document.createElement("img");
        img.src = item.foto;
        img.alt = item.nome;
        img.onerror = function () {
          img.remove();
        };
        linha.appendChild(img);
      }
      linha.appendChild(criar("span", "", item.nome));
      linha.appendChild(criar("strong", "", dinheiro(item.valor)));
      card.appendChild(linha);
    });

    lista.appendChild(card);
  });
}

function mostrarEventos() {
  const lista = pegarId("lista-eventos");
  lista.innerHTML = "";

  eventos.forEach(function (ev) {
    const card = criar("div", "card");
    card.appendChild(criar("h4", "", ev.nome));
    card.appendChild(criar("p", "detalhe", ev.dia + " às " + ev.horario));
    if (ev.descricao) card.appendChild(criar("p", "", ev.descricao));
    lista.appendChild(card);
  });
}

pegarId("busca").addEventListener("input", mostrarLojas);

mostrarChips();
mostrarLojas();
mostrarEventos();
