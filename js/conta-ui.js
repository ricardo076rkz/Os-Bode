// Nordestinando - sino de notificações e botão do perfil no topo das telas
// Depende de icones.js, comum.js e api.js

// preenche o container com [sino] [perfil]; atualiza o contador a cada 30 segundos
function montarAcoesTopo(container, usuario) {
  container.innerHTML = "";
  container.className = "acoes-topo";

  const sino = criar("a", "icone-botao");
  sino.href = "notificacoes.html";
  sino.setAttribute("aria-label", "Notificações");
  sino.appendChild(icone("sino"));
  const contador = criar("span", "contador oculto", "0");
  sino.appendChild(contador);
  container.appendChild(sino);

  const perfil = criar("a", "icone-botao");
  perfil.href = "perfil.html";
  perfil.setAttribute("aria-label", "Meu perfil");
  perfil.appendChild(criar("span", "inicial", inicial(usuario.nome)));
  container.appendChild(perfil);

  api("GET", "/api/conta").then(function (d) {
    aplicarTema(d.conta.preferencias.tema);
    if (d.conta.avatar) {
      const img = document.createElement("img");
      img.alt = "";
      img.src = d.conta.avatar;
      perfil.innerHTML = "";
      perfil.appendChild(img);
    }
  }, function () {});

  function atualizar() {
    if (document.hidden) return;
    api("GET", "/api/notificacoes/contagem").then(function (d) {
      contador.textContent = d.nao_lidas > 99 ? "99+" : d.nao_lidas;
      contador.classList.toggle("oculto", d.nao_lidas === 0);
      sino.setAttribute("aria-label", d.nao_lidas ? "Notificações: " + d.nao_lidas + " novas" : "Notificações");
    }, function () {});
  }
  atualizar();
  setInterval(atualizar, 30000);
  document.addEventListener("visibilitychange", atualizar);
}

// data/hora que o servidor manda (UTC) -> "09/11 às 14:30"
function dataHoraBR(texto) {
  const d = new Date(String(texto).replace(" ", "T") + "Z");
  if (isNaN(d)) return "";
  return d.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" }) + " às " + d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}
