// Tela de entrada: escolher "Sou usuário" ou "Sou comerciante", entrar ou criar conta
// (depende de comum.js e api.js)

const form = pegarId("form-login");
const formConta = pegarId("form-conta");
const msg = pegarId("mensagem");
const abas = document.querySelectorAll(".perfil-opcao input");
let modo = "entrar"; // "entrar" ou "criar"

function perfilEscolhido() {
  return document.querySelector('input[name="perfil"]:checked').value; // CLIENTE ou LOGISTA
}

function atualizarTela() {
  const comerciante = perfilEscolhido() == "LOGISTA";
  msg.className = "mensagem oculto";

  pegarId("descricao-perfil").textContent = comerciante
    ? "Cadastre seu estabelecimento, divulgue seus produtos e eventos e acompanhe as avaliações."
    : "Encontre lojas e serviços no mapa, avalie e reserve itens para retirar.";

  form.classList.toggle("oculto", modo != "entrar");
  formConta.classList.toggle("oculto", modo != "criar" || comerciante);
  pegarId("criar-comerciante").classList.toggle("oculto", modo != "criar" || !comerciante);

  pegarId("trocar-modo").textContent = modo == "entrar" ? "Não tenho conta — criar conta" : "Já tenho conta — entrar";
}

abas.forEach(function (a) {
  a.addEventListener("change", atualizarTela);
});

pegarId("trocar-modo").addEventListener("click", function () {
  modo = modo == "entrar" ? "criar" : "entrar";
  atualizarTela();
});

function irParaAreaDoPerfil(usuario) {
  window.location.href = usuario.perfil == "LOGISTA" ? "minha_loja.html" : "explorar.html";
}

form.addEventListener("submit", async function (e) {
  e.preventDefault();
  try {
    const dados = await api("POST", "/api/login", {
      email: pegarId("email").value,
      senha: pegarId("senha").value,
      perfil: perfilEscolhido()
    });
    irParaAreaDoPerfil(dados.usuario);
  } catch (erro) {
    mostrarMensagem(msg, erro.erro, "erro");
  }
});

mascaraTelefone(pegarId("c-telefone"));

formConta.addEventListener("submit", async function (e) {
  e.preventDefault();
  mostrarErrosCampos(formConta, {});
  try {
    const dados = await api("POST", "/api/cadastro/usuario", {
      nome: pegarId("c-nome").value,
      email: pegarId("c-email").value,
      telefone: pegarId("c-telefone").value,
      senha: pegarId("c-senha").value,
      confirmar_senha: pegarId("c-confirmar").value,
      aceite: pegarId("c-aceite").checked
    });
    irParaAreaDoPerfil(dados.usuario);
  } catch (erro) {
    mostrarErrosCampos(formConta, erro.campos);
    mostrarMensagem(msg, erro.erro, "erro");
  }
});

// quem já está logado vai direto para a sua área
quemSou().then(function (usuario) {
  if (usuario) irParaAreaDoPerfil(usuario);
}, function () {});

atualizarTela();
