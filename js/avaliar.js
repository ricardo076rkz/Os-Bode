// Avaliação detalhada com estimativa de pontos (o cálculo oficial é feito no servidor)
const CRITERIOS = [["atendimento", "Atendimento"], ["qualidade", "Qualidade"], ["preco", "Preço"], ["ambiente", "Ambiente"]];

function seletorEstrelas(nome, valorInicial, aoMudar) {
  const caixa = criar("div", "estrelas-escolha");
  caixa.setAttribute("role", "radiogroup");
  let valor = valorInicial || 0;
  const botoes = [];
  function pintar() {
    botoes.forEach(function (b, i) {
      b.classList.toggle("cheia", i < valor);
      b.setAttribute("aria-checked", i + 1 == valor ? "true" : "false");
    });
  }
  for (let i = 1; i <= 5; i++) {
    const b = criar("button", "estrela-botao", "★");
    b.type = "button";
    b.setAttribute("role", "radio");
    b.setAttribute("aria-label", nome + ": " + i + " de 5");
    b.addEventListener("click", function () {
      valor = valor == i ? 0 : i; // clicar de novo limpa
      pintar();
      aoMudar(valor);
    });
    botoes.push(b);
    caixa.appendChild(b);
  }
  pintar();
  return caixa;
}

function abrirAvaliacao(l, aoConcluir) {
  const d = pegarId("dialogo-avaliar");
  d.innerHTML = "";
  const dados = { nota: 0, crit_atendimento: 0, crit_qualidade: 0, crit_preco: 0, crit_ambiente: 0, comentario: "", dica: "", consumiu: "", foto: "" };
  const form = criar("form", "form-avaliar");
  form.noValidate = true;
  const titulo = criar("h2", "", "Avaliar " + l.nome);
  titulo.id = "avaliar-titulo";
  form.appendChild(titulo);
  const erro = criar("p", "mensagem erro oculto");
  erro.setAttribute("role", "alert");

  const nota = criar("div", "campo-aval");
  nota.appendChild(criar("label", "", "Nota geral (obrigatória)"));
  nota.appendChild(seletorEstrelas("Nota geral", 0, function (v) { dados.nota = v; }));
  form.appendChild(nota);

  const grade = criar("div", "criterios");
  CRITERIOS.forEach(function (c) {
    const linha = criar("div", "campo-aval");
    linha.appendChild(criar("span", "rotulo-crit", c[1]));
    linha.appendChild(seletorEstrelas(c[1], 0, function (v) { dados["crit_" + c[0]] = v; estimar(); }));
    grade.appendChild(linha);
  });
  form.appendChild(criar("p", "dica-form", "Avalie pelo menos 2 critérios para ganhar pontos. A nota, boa ou ruim, não muda seus pontos."));
  form.appendChild(grade);

  function campo(rotulo, el) {
    const w = criar("div", "campo-aval");
    const lb = criar("label", "", rotulo);
    el.id = "av-" + rotulo.length + rotulo.charCodeAt(0);
    lb.htmlFor = el.id;
    w.appendChild(lb);
    w.appendChild(el);
    form.appendChild(w);
  }
  const coment = document.createElement("textarea"); coment.maxLength = 600; coment.rows = 3; coment.placeholder = "Conte como foi a sua experiência";
  coment.addEventListener("input", function () { dados.comentario = coment.value; estimar(); });
  campo("Comentário", coment);
  const dica = document.createElement("input"); dica.type = "text"; dica.maxLength = 200; dica.placeholder = "Uma dica para quem vai visitar";
  dica.addEventListener("input", function () { dados.dica = dica.value; estimar(); });
  campo("Dica para outros visitantes", dica);
  const cons = document.createElement("input"); cons.type = "text"; cons.maxLength = 80; cons.placeholder = "Ex.: cuscuz com carne de sol";
  cons.addEventListener("input", function () { dados.consumiu = cons.value; estimar(); });
  campo("O que você consumiu?", cons);
  const foto = document.createElement("input"); foto.type = "file"; foto.accept = "image/*";
  const previa = criar("img", "previa-foto oculto"); previa.alt = "Prévia da foto";
  foto.addEventListener("change", function () {
    reduzirFoto(foto.files[0], 700, function (url) {
      dados.foto = url;
      previa.src = url;
      previa.classList.toggle("oculto", !url);
      estimar();
    });
  });
  campo("Foto (opcional)", foto);
  form.appendChild(previa);

  const est = criar("div", "estimativa");
  est.setAttribute("aria-live", "polite");
  form.appendChild(est);
  form.appendChild(erro);

  const bt = criar("div", "botoes-linha");
  const cancelar = criar("button", "botao contorno", "Cancelar"); cancelar.type = "button";
  cancelar.addEventListener("click", function () { d.close(); });
  const enviar = criar("button", "botao", "Enviar avaliação"); enviar.type = "submit";
  bt.appendChild(cancelar); bt.appendChild(enviar);
  form.appendChild(bt);

  let temporizador = null;
  let seq = 0;
  function estimar() {
    clearTimeout(temporizador);
    temporizador = setTimeout(async function () {
      const minha = ++seq;
      try {
        const r = await api("POST", "/api/pontos/estimativa", Object.assign({ id_loja: l.id }, dados));
        if (minha != seq) return;
        const e = r.estimativa;
        est.innerHTML = "";
        if (!e.valido) { est.appendChild(criar("p", "est-aviso", e.motivo)); return; }
        est.appendChild(criar("strong", "est-total", "Você deve ganhar " + e.a_receber + " pontos"));
        e.itens.forEach(function (i) { est.appendChild(criar("span", "est-item", "+" + i.pontos + " " + i.rotulo)); });
        if (e.premium) est.appendChild(criar("span", "est-item premium", "Nordestinando+ dobra os pontos"));
        else est.appendChild(criar("a", "est-link", "Com o Nordestinando+ seriam " + e.base * 2 + " pontos")).href = "premium.html";
        if (e.ja_pontuado) est.appendChild(criar("span", "est-item", "Você já ganhou " + e.ja_pontuado + " pontos base nesta loja; só a diferença conta."));
        est.appendChild(criar("small", "", "Estimativa. O valor final é calculado pelo servidor ao enviar."));
      } catch (x) {}
    }, 300);
  }
  estimar();

  form.addEventListener("submit", async function (ev) {
    ev.preventDefault();
    erro.classList.add("oculto");
    if (!dados.nota) { erro.textContent = "Escolha a nota geral de 1 a 5."; erro.classList.remove("oculto"); return; }
    enviar.disabled = true;
    try {
      const corpo = {};
      Object.keys(dados).forEach(function (k) { if (dados[k] !== 0 && dados[k] !== "") corpo[k] = dados[k]; });
      const r = await api("POST", "/api/lojas/" + l.id + "/avaliacoes", corpo);
      mostrarConfirmacao(r.ganho);
      if (aoConcluir) aoConcluir();
    } catch (x) {
      erro.textContent = x.erro || "Não foi possível enviar.";
      erro.classList.remove("oculto");
      enviar.disabled = false;
    }
  });

  function mostrarConfirmacao(g) {
    d.innerHTML = "";
    const caixa = criar("div", "confirmacao");
    caixa.appendChild(criar("h2", "", "Avaliação enviada"));
    if (g.pontos > 0) {
      caixa.appendChild(criar("p", "conf-pontos", "+" + g.pontos + " pontos"));
      if (g.bonus > 0) caixa.appendChild(criar("p", "", "Inclui " + g.bonus + " de bônus Nordestinando+."));
      g.itens.forEach(function (i) { caixa.appendChild(criar("span", "est-item", "+" + i.pontos + " " + i.rotulo)); });
    } else {
      caixa.appendChild(criar("p", "", g.motivo || "Obrigado por ajudar outros visitantes."));
    }
    const bt2 = criar("div", "botoes-linha");
    const cart = criar("a", "botao contorno", "Ver minha carteira"); cart.href = "carteira.html";
    const ok = criar("button", "botao", "Fechar"); ok.type = "button";
    ok.addEventListener("click", function () { d.close(); });
    bt2.appendChild(cart); bt2.appendChild(ok);
    caixa.appendChild(bt2);
    d.appendChild(caixa);
  }

  d.appendChild(form);
  d.showModal();
}
