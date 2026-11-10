// Configurações - Nordestinando (tudo é salvo na conta, no servidor)
const msg = pegarId("mensagem");
let conta = null;

function aviso(texto, tipo) {
  mostrarMensagem(msg, texto, tipo);
  msg.scrollIntoView({ block: "nearest" });
}

async function salvarPref(corpo, textoOk) {
  try {
    const r = await api("PUT", "/api/conta/preferencias", corpo);
    conta.preferencias = r.preferencias;
    aviso(textoOk || "Preferência salva.", "ok");
    return true;
  } catch (e) {
    aviso(e.erro, "erro");
    desenharPrefs(); // volta o interruptor para o valor real
    return false;
  }
}

function desenharPrefs() {
  const p = conta.preferencias;
  document.querySelectorAll('input[name="tema"]').forEach(function (r) { r.checked = r.value == p.tema; });
  document.querySelectorAll("[data-notif]").forEach(function (c) { c.checked = p.notif[c.dataset.notif]; });
  pegarId("priv-nome").checked = p.privacidade.nome_nas_avaliacoes;
}

document.querySelectorAll('input[name="tema"]').forEach(function (r) {
  r.addEventListener("change", async function () {
    aplicarTema(r.value); // muda na hora
    await salvarPref({ tema: r.value }, "Tema salvo.");
  });
});
document.querySelectorAll("[data-notif]").forEach(function (c) {
  c.addEventListener("change", function () {
    const corpo = { notif: {} };
    corpo.notif[c.dataset.notif] = c.checked;
    salvarPref(corpo);
  });
});
pegarId("priv-nome").addEventListener("change", function (e) {
  salvarPref({ privacidade: { nome_nas_avaliacoes: e.target.checked } });
});

// ---------- sessões
async function carregarSessoes() {
  const area = pegarId("sessoes");
  try {
    const lista = (await api("GET", "/api/conta/sessoes")).sessoes;
    area.innerHTML = "";
    lista.forEach(function (s) {
      const linha = criar("div", "lista-item");
      const t = criar("div");
      const nome = criar("strong", "", s.agente || "Aparelho");
      if (s.atual) nome.appendChild(criar("span", "atual-selo", " · este aparelho"));
      t.appendChild(nome);
      t.appendChild(criar("small", "", "Último uso: " + dataHoraBR(s.ultimo_uso)));
      linha.appendChild(t);
      if (!s.atual) {
        const b = criar("button", "botao contorno", "Desconectar");
        b.type = "button";
        b.addEventListener("click", async function () {
          b.disabled = true;
          try {
            await api("DELETE", "/api/conta/sessoes/" + s.id);
            aviso("Aparelho desconectado.", "ok");
          } catch (e) { aviso(e.erro, "erro"); }
          carregarSessoes();
        });
        linha.appendChild(b);
      }
      area.appendChild(linha);
    });
    pegarId("encerrar-outras").classList.toggle("oculto", lista.length < 2);
  } catch (e) {
    area.innerHTML = "";
    area.appendChild(criar("p", "mensagem erro", e.erro));
  }
}
pegarId("encerrar-outras").addEventListener("click", async function () {
  if (!confirm("Desconectar todos os outros aparelhos?")) return;
  try {
    const r = await api("POST", "/api/conta/sessoes/encerrar-outras");
    aviso(r.encerradas + " aparelho(s) desconectado(s).", "ok");
  } catch (e) { aviso(e.erro, "erro"); }
  carregarSessoes();
});

// ---------- excluir conta (senha + digitar EXCLUIR)
const formExcluir = pegarId("form-excluir");
pegarId("abrir-excluir").addEventListener("click", function () {
  formExcluir.classList.remove("oculto");
  pegarId("abrir-excluir").classList.add("oculto");
  pegarId("x-senha").focus();
});
pegarId("cancelar-excluir").addEventListener("click", function () {
  formExcluir.reset();
  mostrarErrosCampos(formExcluir, {});
  formExcluir.classList.add("oculto");
  pegarId("abrir-excluir").classList.remove("oculto");
});
formExcluir.addEventListener("submit", async function (e) {
  e.preventDefault();
  const botao = formExcluir.querySelector("button[type=submit]");
  mostrarErrosCampos(formExcluir, {});
  botao.disabled = true;
  try {
    await api("DELETE", "/api/conta", { senha: formExcluir.senha.value, confirmacao: formExcluir.confirmacao.value });
    try { localStorage.removeItem("tema"); } catch (x) {}
    window.location.href = "../index.html";
  } catch (erro) {
    mostrarErrosCampos(formExcluir, erro.campos || {});
    aviso(erro.erro, "erro");
    botao.disabled = false;
  }
});

async function iniciar() {
  try {
    conta = (await api("GET", "/api/conta")).conta;
  } catch (e) {
    if (e.status == 401) { window.location.href = "tela.html"; return; }
    pegarId("carregando").classList.add("oculto");
    aviso(e.erro, "erro");
    return;
  }
  pegarId("carregando").classList.add("oculto");
  pegarId("conteudo").classList.remove("oculto");
  pegarId("o-que-apaga").textContent = conta.perfil == "LOGISTA"
    ? "seus dados, sua loja, vitrine, eventos e avaliações recebidas."
    : "seus dados, avaliações e pedidos.";
  desenharPrefs();
  carregarSessoes();
}
iniciar();


// ---------- LGPD: baixar meus dados ----------
pegarId("baixar-dados").addEventListener("click", async function () {
  try {
    const dados = await api("GET", "/api/lgpd/meus-dados");
    const arq = new Blob([JSON.stringify(dados, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(arq);
    a.download = "meus-dados-nordestinando.json";
    document.body.appendChild(a);
    a.click();
    a.remove();
    aviso("Download iniciado.", "ok");
  } catch (e) {
    aviso(e.erro || "Não foi possível gerar o arquivo.", "erro");
  }
});
api("GET", "/api/lgpd/aceite").then(function (d) {
  const ult = d.aceitou.privacidade;
  pegarId("aceite-info").textContent = ult ? "Você aceitou a versão " + ult + " dos documentos." : "";
}, function () {});
