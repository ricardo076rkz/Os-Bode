// Cadastro do comerciante em 4 etapas (depende de comum.js, api.js e mapa.js)

const formCad = pegarId("form-cadastro");
const etapas = formCad.querySelectorAll(".etapa");
const bolinhas = document.querySelectorAll(".passo");
const btnVoltar = pegarId("btn-voltar");
const btnProximo = pegarId("btn-proximo");
const msgCad = pegarId("mensagem");
let etapaAtual = 0;
let localizacao = null;
let logo = "";
let foto = "";

// segmentos vêm do servidor (mesma lista que ele valida)
api("GET", "/api/config").then(function (c) {
  const select = pegarId("segmento");
  c.segmentos.forEach(function (s) {
    const o = document.createElement("option");
    o.textContent = s;
    select.appendChild(o);
  });
}, function (erro) {
  mostrarMensagem(msgCad, erro.erro, "erro");
});

mascaraTelefone(pegarId("telefone"));
mascaraTelefone(pegarId("telefone_comercial"));
mascaraTelefone(pegarId("whatsapp"));
mascaraCNPJ(pegarId("cnpj"));
mascaraCEP(pegarId("cep"));
montarHorarios(pegarId("horarios"));

function mostrarEtapa(n) {
  etapaAtual = n;
  etapas.forEach(function (e, i) {
    e.classList.toggle("oculto", i != n);
  });
  bolinhas.forEach(function (b, i) {
    b.classList.toggle("ativo", i == n);
    b.classList.toggle("feito", i < n);
  });
  btnVoltar.classList.toggle("oculto", n == 0);
  btnProximo.textContent = n == etapas.length - 1 ? "Finalizar cadastro" : "Próximo";
  msgCad.className = "mensagem oculto";
  document.querySelector(".tela").scrollTop = 0;

  // o mapa só é criado quando a etapa 3 aparece (escondido ele ficaria com tamanho zero)
  if (n == 2 && !localizacao) {
    localizacao = iniciarLocalizacao({
      cep: pegarId("cep"), rua: pegarId("rua"), numero: pegarId("numero"), bairro: pegarId("bairro"),
      cidade: pegarId("cidade"), estado: pegarId("estado"),
      lat: pegarId("latitude"), lng: pegarId("longitude"),
      botao: pegarId("btn-localizar"), mapa: pegarId("mapa"), aviso: pegarId("aviso-mapa")
    });
  }
}

// valida os campos da etapa (usa as regras do HTML: required, minlength...)
function etapaValida(n) {
  mostrarErrosCampos(formCad, {});
  const campos = etapas[n].querySelectorAll("input, select, textarea");
  for (const campo of campos) {
    if (!campo.checkValidity()) {
      campo.reportValidity();
      return false;
    }
  }
  if (n == 0 && pegarId("senha").value != pegarId("confirmar_senha").value) {
    mostrarErrosCampos(formCad, { confirmar_senha: "As senhas não são iguais." });
    return false;
  }
  if (n == 0 && !(/[A-Za-z]/.test(pegarId("senha").value) && /\d/.test(pegarId("senha").value))) {
    mostrarErrosCampos(formCad, { senha: "Use letras e números na senha." });
    return false;
  }
  if (n == 1 && pegarId("cnpj").value && !pegarId("razao_social").value.trim()) {
    mostrarErrosCampos(formCad, { razao_social: "Informe a razão social do CNPJ." });
    return false;
  }
  return true;
}

btnVoltar.addEventListener("click", function () {
  mostrarEtapa(etapaAtual - 1);
});

btnProximo.addEventListener("click", function () {
  if (!etapaValida(etapaAtual)) return;
  if (etapaAtual < etapas.length - 1) {
    mostrarEtapa(etapaAtual + 1);
  } else {
    enviar();
  }
});

// fotos: reduz antes de mandar
pegarId("logo").addEventListener("change", function () {
  reduzirFoto(this.files[0], 300, function (d) { logo = d; });
});
pegarId("foto").addEventListener("change", function () {
  reduzirFoto(this.files[0], 700, function (d) { foto = d; });
});

function valor(id) {
  return pegarId(id).value;
}

async function enviar() {
  btnProximo.disabled = true;
  const corpo = {
    nome: valor("nome"), email: valor("email"), telefone: valor("telefone"),
    senha: valor("senha"), confirmar_senha: valor("confirmar_senha"),
    nome_fantasia: valor("nome_fantasia"), segmento: valor("segmento"), descricao: valor("descricao"),
    cnpj: valor("cnpj"), razao_social: valor("razao_social"),
    telefone_comercial: valor("telefone_comercial"), whatsapp: valor("whatsapp"),
    instagram: valor("instagram"), site: valor("site"), logo: logo, foto: foto,
    cep: valor("cep"), rua: valor("rua"), numero: valor("numero"), bairro: valor("bairro"),
    cidade: valor("cidade"), estado: valor("estado"),
    latitude: valor("latitude"), longitude: valor("longitude"),
    horarios: lerHorarios(pegarId("horarios")),
    aceite: pegarId("aceite").checked
  };

  try {
    await api("POST", "/api/cadastro/comerciante", corpo);
    window.location.href = "minha_loja.html";
  } catch (erro) {
    // volta para a primeira etapa que tem campo com erro
    const nomes = Object.keys(erro.campos);
    for (let i = 0; i < etapas.length; i++) {
      const tem = nomes.some(function (nome) {
        return etapas[i].querySelector('[name="' + nome + '"]') || (nome == "horarios" && i == 3);
      });
      if (tem) {
        mostrarEtapa(i);
        break;
      }
    }
    mostrarErrosCampos(formCad, erro.campos);
    mostrarMensagem(msgCad, erro.campos.horarios || erro.erro, "erro");
  } finally {
    btnProximo.disabled = false;
  }
}

mostrarEtapa(0);
