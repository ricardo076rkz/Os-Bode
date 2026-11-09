// Nordestinando - ícones em SVG (traço simples, todos 24x24)
// Uso no HTML:  <i data-icone="casa"></i>   (a cor vem do texto: color / currentColor)

const ICONES = {
  casa: '<path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/>',
  sacola: '<path d="M5 8h14l-1 12H6L5 8z"/><path d="M9 8a3 3 0 016 0"/>',
  calendario: '<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M4 10h16M9 3v4M15 3v4"/>',
  estrela: '<path d="M12 3l2.8 5.7 6.2.9-4.5 4.4 1.1 6.2L12 17.2 6.4 20.2l1.1-6.2L3 9.6l6.2-.9z"/>',
  grafico: '<path d="M5 20V11M12 20V4M19 20v-6"/>',
  pino: '<path d="M12 21s-7-6.2-7-11a7 7 0 0114 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>',
  busca: '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>',
  pessoa: '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-6 8-6s8 2 8 6"/>',
  sair: '<path d="M9 4H5v16h4"/><path d="M16 8l4 4-4 4M20 12H9"/>',
  relogio: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  rota: '<path d="M3 11l18-8-8 18-2-8-8-2z"/>',
  loja: '<path d="M4 9l1-5h14l1 5"/><path d="M4 9a3 3 0 006 0 3 3 0 006 0 3 3 0 004 0"/><path d="M5 12v8h14v-8M10 20v-5h4v5"/>',
  lapis: '<path d="M4 20h4L19 9l-4-4L4 16v4z"/><path d="M14 6l4 4"/>',
  mais: '<path d="M12 5v14M5 12h14"/>',
  sol: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5L19 19M5 19l1.5-1.5M17.5 6.5L19 5"/>',
  nuvem: '<path d="M7 18a4 4 0 010-8 5 5 0 019.6-1A4.5 4.5 0 0117 18H7z"/>',
  chuva: '<path d="M7 15a4 4 0 010-8 5 5 0 019.6-1A4.5 4.5 0 0117 15H7z"/><path d="M8 18l-1 3M12 18l-1 3M16 18l-1 3"/>',
  telefone: '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 005 5L15 13l5 2v4a2 2 0 01-2 2A16 16 0 013 6a2 2 0 012-2z"/>',
  conversa: '<path d="M4 5h16v11H9l-5 4V5z"/>',
  voltar: '<path d="M19 12H5M11 6l-6 6 6 6"/>',
  sino: '<path d="M6 16V11a6 6 0 0112 0v5l1.5 2h-15L6 16z"/><path d="M10 21h4"/>',
  engrenagem: '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/>',
  cadeado: '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 018 0v3"/>',
  camera: '<path d="M4 8h3l2-3h6l2 3h3v12H4V8z"/><circle cx="12" cy="13" r="3.5"/>',
  lixeira: '<path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/>',
  check: '<path d="M5 12.5l4.5 4.5L19 7"/>',
  escudo: '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6l8-3z"/><path d="M9 12l2 2 4-4"/>',
  loja_grande: '<path d="M3 9l1.5-5h15L21 9"/><path d="M3 9a3.3 3.3 0 006 0 3.3 3.3 0 006 0 3.3 3.3 0 006 0"/><path d="M5 12v8h14v-8M10 20v-5h4v5"/>'
};

function desenharIcones(raiz) {
  (raiz || document).querySelectorAll("[data-icone]").forEach(function (el) {
    if (el.firstChild) return; // já desenhado
    const caminho = ICONES[el.dataset.icone];
    if (!caminho) return;
    el.setAttribute("aria-hidden", "true");
    el.innerHTML = '<svg viewBox="0 0 24 24" focusable="false">' + caminho + "</svg>";
  });
}

// devolve um <i> pronto, para os scripts que montam a tela por código
function icone(nome) {
  const el = document.createElement("i");
  el.dataset.icone = nome;
  desenharIcones({ querySelectorAll: function () { return [el]; } });
  return el;
}

document.addEventListener("DOMContentLoaded", function () {
  desenharIcones();
});
