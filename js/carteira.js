// Minha carteira - pontos, recompensas, vouchers e extrato
let aba = "recompensas";
let filtroExtrato = "todos";
const lista = pegarId("lista");
const msg = pegarId("mensagem");

function vazio(titulo, texto, link) {
  const caixa = criar("div", "estado-vazio");
  caixa.appendChild(criar("strong", "", titulo));
  caixa.appendChild(criar("span", "", texto));
  if (link) {
    const a = criar("a", "botao", link[0]);
    a.href = link[1];
    caixa.appendChild(a);
  }
  return caixa;
}

function pts(n) {
  return n + (Math.abs(n) == 1 ? " ponto" : " pontos");
}

async function carregarSaldo() {
  const d = await api("GET", "/api/carteira");
  const c = d.carteira;
  pegarId("saldo").textContent = c.saldo;
  pegarId("t-ganho").textContent = c.total_ganho;
  pegarId("t-usado").textContent = c.total_usado;
  pegarId("t-bonus").textContent = c.bonus_premium;
  pegarId("nivel-nome").textContent = "Nível " + c.nivel.nome;
  pegarId("nivel-prox").textContent = c.nivel.proximo ? "faltam " + c.nivel.faltam + " para " + c.nivel.proximo : "Nível máximo";
  pegarId("barra-preench").style.width = c.nivel.progresso + "%";
  pegarId("barra").setAttribute("aria-valuenow", c.nivel.progresso);
  const selo = pegarId("selo-plano");
  const ativo = c.plano.estado == "premium_ativo";
  selo.textContent = ativo ? "Nordestinando+ · pontos 2x" : "Conhecer Nordestinando+";
  selo.classList.toggle("premium", ativo);
}

function abrirVoucher(v) {
  const d = pegarId("dialogo-voucher");
  d.innerHTML = "";
  d.appendChild(criar("h2", "", v.titulo)).id = "voucher-titulo";
  d.appendChild(criar("p", "voucher-loja", v.loja.nome));
  const cod = criar("div", "voucher-codigo", v.codigo);
  d.appendChild(cod);
  d.appendChild(criar("p", "voucher-ajuda", v.estado == "resgatado" ? "Mostre este código no balcão. Ele vale uma vez só." : "Este voucher está " + v.estado_rotulo.toLowerCase() + "."));
  [["Benefício", v.beneficio], ["Estado", v.estado_rotulo], ["Válido até", dataBR(v.validade)], ["Pontos usados", v.pontos]].forEach(function (p) {
    const l = criar("div", "dado-linha");
    l.appendChild(criar("span", "", p[0]));
    l.appendChild(criar("span", "", String(p[1])));
    d.appendChild(l);
  });
  if (v.condicoes) d.appendChild(criar("p", "voucher-ajuda", "Condições: " + v.condicoes));
  const bt = criar("div", "botoes-linha");
  const copiar = criar("button", "botao contorno", "Copiar código");
  copiar.type = "button";
  copiar.addEventListener("click", function () {
    if (navigator.clipboard) navigator.clipboard.writeText(v.codigo).then(function () { copiar.textContent = "Código copiado"; });
  });
  const fechar = criar("button", "botao", "Fechar");
  fechar.type = "button";
  fechar.addEventListener("click", function () { d.close(); });
  bt.appendChild(copiar);
  bt.appendChild(fechar);
  d.appendChild(bt);
  d.showModal();
}

async function mostrarRecompensas() {
  const d = await api("GET", "/api/recompensas");
  lista.innerHTML = "";
  if (!d.recompensas.length) {
    lista.appendChild(vazio("Nenhuma recompensa por enquanto", "Quando as lojas parceiras publicarem promoções, elas aparecem aqui. Continue avaliando para juntar pontos.", ["Avaliar lojas", "explorar.html"]));
    return;
  }
  d.recompensas.forEach(function (r) {
    const el = criar("article", "recompensa");
    const topo = criar("div", "recompensa-topo");
    topo.appendChild(criar("span", "selo-beneficio", r.beneficio));
    topo.appendChild(criar("span", "recompensa-custo", pts(r.pontos)));
    el.appendChild(topo);
    el.appendChild(criar("h3", "", r.titulo));
    el.appendChild(criar("p", "recompensa-loja", r.loja.nome + (r.loja.bairro ? " · " + r.loja.bairro : "")));
    el.appendChild(criar("p", "", r.descricao));
    const meta = criar("p", "recompensa-meta", "Válida até " + dataBR(r.validade) + " · restam " + r.restantes);
    el.appendChild(meta);
    if (r.condicoes) el.appendChild(criar("p", "recompensa-meta", "Condições: " + r.condicoes));
    const b = criar("button", "botao", r.pode_resgatar ? "Resgatar por " + pts(r.pontos) : r.ja_resgatou >= r.limite_por_usuario ? "Limite atingido" : "Faltam " + pts(r.faltam));
    b.type = "button";
    b.disabled = !r.pode_resgatar;
    b.addEventListener("click", function () {
      if (!confirm("Resgatar “" + r.titulo + "” por " + pts(r.pontos) + "?")) return;
      b.disabled = true;
      api("POST", "/api/recompensas/" + r.id + "/resgatar").then(async function (res) {
        mostrarMensagem(msg, "Voucher resgatado! Código " + res.voucher.codigo + ". Saldo: " + pts(res.voucher.saldo) + ".", "ok");
        await carregarSaldo();
        mostrarRecompensas();
      }, function (erro) {
        mostrarMensagem(msg, erro.erro, "erro");
        b.disabled = false;
      });
    });
    el.appendChild(b);
    lista.appendChild(el);
  });
}

async function mostrarVouchers() {
  const d = await api("GET", "/api/carteira/vouchers");
  lista.innerHTML = "";
  if (!d.vouchers.length) {
    lista.appendChild(vazio("Você ainda não tem vouchers", "Troque seus pontos por uma recompensa na aba Recompensas.", null));
    return;
  }
  d.vouchers.forEach(function (v) {
    const el = criar("button", "voucher-item estado-" + v.estado);
    el.type = "button";
    const esq = criar("div", "");
    esq.appendChild(criar("strong", "", v.titulo));
    esq.appendChild(criar("small", "", v.loja.nome + " · até " + dataBR(v.validade)));
    el.appendChild(esq);
    el.appendChild(criar("span", "selo-estado", v.estado_rotulo));
    el.addEventListener("click", function () { abrirVoucher(v); });
    lista.appendChild(el);
  });
}

function desenharFiltros() {
  const caixa = pegarId("filtro-extrato");
  caixa.innerHTML = "";
  [["todos", "Tudo"], ["ganhos", "Ganhos"], ["usos", "Usos"], ["bonus", "Bônus"]].forEach(function (f) {
    const c = criar("button", "chip" + (filtroExtrato == f[0] ? " ativo" : ""), f[1]);
    c.type = "button";
    c.addEventListener("click", function () { filtroExtrato = f[0]; desenharFiltros(); mostrarExtrato(); });
    caixa.appendChild(c);
  });
}

async function mostrarExtrato() {
  const d = await api("GET", "/api/carteira/movimentos?tipo=" + filtroExtrato);
  lista.innerHTML = "";
  if (!d.movimentos.length) {
    lista.appendChild(vazio("Sem movimentações", "Cada avaliação, resgate e estorno aparece aqui com data e saldo.", ["Avaliar uma loja", "explorar.html"]));
    return;
  }
  d.movimentos.forEach(function (m) {
    const el = criar("div", "movimento");
    const esq = criar("div", "");
    esq.appendChild(criar("strong", "", m.descricao));
    let det = dataHoraBR(m.criado_em);
    if (m.pontos_bonus > 0) det += " · inclui " + m.pontos_bonus + " de bônus Nordestinando+";
    esq.appendChild(criar("small", "", det));
    el.appendChild(esq);
    const dir = criar("div", "movimento-valor " + (m.pontos > 0 ? "mais" : "menos"));
    dir.appendChild(criar("strong", "", (m.pontos > 0 ? "+" : "") + m.pontos));
    dir.appendChild(criar("small", "", "saldo " + m.saldo_apos));
    el.appendChild(dir);
    lista.appendChild(el);
  });
}

function trocarAba(nova) {
  aba = nova;
  ["recompensas", "vouchers", "extrato"].forEach(function (a) {
    pegarId("aba-" + a).setAttribute("aria-selected", a == aba ? "true" : "false");
  });
  pegarId("filtro-extrato").classList.toggle("oculto", aba != "extrato");
  lista.innerHTML = "";
  for (let i = 0; i < 2; i++) lista.appendChild(criar("div", "esqueleto"));
  const f = { recompensas: mostrarRecompensas, vouchers: mostrarVouchers, extrato: mostrarExtrato }[aba];
  f().catch(function (erro) { mostrarMensagem(msg, erro.erro || "Não foi possível carregar.", "erro"); });
}

["recompensas", "vouchers", "extrato"].forEach(function (a) {
  pegarId("aba-" + a).addEventListener("click", function () { trocarAba(a); });
});

(async function () {
  try {
    await carregarSaldo();
  } catch (erro) {
    if (erro.status == 401 || erro.status == 403) {
      lista.appendChild(vazio("Carteira só para usuários", "Entre como usuário para ver seus pontos.", ["Entrar", "tela.html"]));
      return;
    }
  }
  desenharFiltros();
  trocarAba("recompensas");
})();
