// Nordestinando - conversa com o servidor (python/app.py)
// Precisa abrir o site por http://localhost:5000 (não clicando direto no arquivo .html)

async function api(metodo, url, corpo) {
  const opcoes = { method: metodo, headers: {}, credentials: "same-origin" };
  if (corpo !== undefined) {
    opcoes.headers["Content-Type"] = "application/json";
    opcoes.body = JSON.stringify(corpo);
  }

  let resposta;
  try {
    resposta = await fetch(url, opcoes);
  } catch (e) {
    throw { erro: "Não consegui falar com o servidor. Ele está rodando? (python python/app.py)", campos: {}, status: 0 };
  }

  let dados = {};
  try {
    dados = await resposta.json();
  } catch (e) {
    throw { erro: "Resposta inesperada do servidor. Abra o site por http://localhost:5000", campos: {}, status: resposta.status };
  }

  if (!resposta.ok) {
    throw { erro: dados.erro || "Erro inesperado.", campos: dados.campos || {}, status: resposta.status };
  }
  return dados;
}

// quem está logado (ou null)
async function quemSou() {
  const dados = await api("GET", "/api/eu");
  return dados.usuario;
}

// mostra os erros embaixo de cada campo (o servidor devolve {campo: mensagem})
function mostrarErrosCampos(form, campos) {
  form.querySelectorAll(".erro-campo").forEach(function (e) {
    e.remove();
  });
  Object.keys(campos).forEach(function (nome) {
    const input = form.querySelector('[name="' + nome + '"]');
    if (!input) return;
    const aviso = document.createElement("small");
    aviso.className = "erro-campo";
    aviso.textContent = campos[nome];
    input.insertAdjacentElement("afterend", aviso);
  });
}

function mostrarMensagem(elemento, texto, tipo) {
  elemento.textContent = texto;
  elemento.className = "mensagem " + (tipo || "erro");
}

// reduz a foto antes de enviar (devolve um data URL jpeg)
function reduzirFoto(arquivo, largura, depois) {
  if (!arquivo) {
    depois("");
    return;
  }
  const leitor = new FileReader();
  leitor.onload = function () {
    const img = new Image();
    img.onload = function () {
      const escala = Math.min(1, largura / img.width);
      const canvas = document.createElement("canvas");
      canvas.width = Math.round(img.width * escala);
      canvas.height = Math.round(img.height * escala);
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
