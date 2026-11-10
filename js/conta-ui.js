// Nordestinando - sino de notificações e botão do perfil no topo das telas
// Depende de icones.js, comum.js e api.js

// preenche o container com [sino] [perfil]; atualiza o contador a cada 30 segundos
function montarAcoesTopo(container, usuario) {
  container.innerHTML = "";
  container.className = "acoes-topo";

  if (usuario.perfil == "CLIENTE") {
    const moedas = criar("a", "chip-pontos oculto");
    moedas.href = "carteira.html";
    moedas.appendChild(icone("moeda"));
    const num = criar("span", "", "0");
    moedas.appendChild(num);
    moedas.setAttribute("aria-label", "Minha carteira de pontos");
    container.appendChild(moedas);
    api("GET", "/api/carteira").then(function (d) {
      num.textContent = d.carteira.saldo;
      moedas.classList.remove("oculto");
    }, function () {});
  }

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

  verificarAceite();

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


// contas antigas, ou mudança de versão dos documentos: pede um novo aceite
function verificarAceite() {
  api("GET", "/api/lgpd/aceite").then(function (d) {
    if (!d.precisa_reaceitar || document.getElementById("dialogo-aceite")) return;
    const dlg = document.createElement("dialog");
    dlg.id = "dialogo-aceite";
    dlg.addEventListener("cancel", function (e) { e.preventDefault(); });
    dlg.appendChild(criar("h2", "", "Atualizamos nossos documentos"));
    const p = criar("p", "");
    p.appendChild(document.createTextNode("Para continuar, leia e aceite os "));
    [["Termos de Uso", "termos.html"], [" e a Política de Privacidade", "privacidade.html"]].forEach(function (l, i) {
      const a = criar("a", "", l[0].trim());
      a.href = l[1]; a.target = "_blank"; a.rel = "noopener";
      if (i) p.appendChild(document.createTextNode(" e a "));
      p.appendChild(a);
    });
    dlg.appendChild(p);
    const lb = criar("label", "aceite");
    const cb = document.createElement("input"); cb.type = "checkbox";
    lb.appendChild(cb); lb.appendChild(criar("span", "", "Li e aceito."));
    dlg.appendChild(lb);
    const msgE = criar("p", "mensagem erro oculto");
    dlg.appendChild(msgE);
    const bt = criar("button", "botao", "Continuar"); bt.type = "button";
    bt.addEventListener("click", function () {
      if (!cb.checked) { mostrarMensagem(msgE, "Marque a caixa para continuar.", "erro"); return; }
      api("POST", "/api/lgpd/aceite", { aceite: true }).then(function () { dlg.close(); dlg.remove(); }, function (e) { mostrarMensagem(msgE, e.erro, "erro"); });
    });
    dlg.appendChild(bt);
    document.body.appendChild(dlg);
    dlg.showModal();
  }, function () {});
}
