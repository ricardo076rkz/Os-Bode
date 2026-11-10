// Página inicial - Nordestinando: mostra o que está na agenda da cidade (dados reais do servidor)
(async function () {
  const area = document.getElementById("agenda-home");
  try {
    const dados = await api("GET", "/api/agenda");
    area.innerHTML = "";
    if (!dados.eventos.length) {
      area.appendChild(criar("p", "vazio", "Nenhum evento na agenda por enquanto."));
      return;
    }
    dados.eventos.slice(0, 4).forEach(function (ev) {
      const cartao = criar("a", "card agenda-mini");
      cartao.href = "html/explorar.html#eventos";
      cartao.appendChild(criar("span", "selo-periodo periodo-" + ev.periodo, ev.dia + " · " + ev.periodo_rotulo));
      cartao.appendChild(criar("strong", "", ev.titulo));
      cartao.appendChild(criar("small", "", ev.local));
      area.appendChild(cartao);
    });
  } catch (erro) {
    area.innerHTML = "";
    area.appendChild(criar("p", "vazio", "Não consegui carregar a agenda agora. Abra o site por http://localhost:5000."));
  }
})();
