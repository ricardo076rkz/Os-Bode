// Login do comerciante (depende de comum.js e api.js)
const msg = pegarId("mensagem");

pegarId("form-login").addEventListener("submit", async function (e) {
  e.preventDefault();
  try {
    await api("POST", "/api/login", {
      email: pegarId("email").value,
      senha: pegarId("senha").value,
      perfil: "LOGISTA"
    });
    window.location.href = "minha_loja.html";
  } catch (erro) {
    mostrarMensagem(msg, erro.erro, "erro");
  }
});

quemSou().then(function (usuario) {
  if (usuario && usuario.perfil == "LOGISTA") window.location.href = "minha_loja.html";
}, function () {});
