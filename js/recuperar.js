// Recuperar senha - Nordestinando
// O envio de e-mail ainda não existe: a tela avisa isso, em vez de fingir que enviou

document.getElementById("form-recuperar").addEventListener("submit", function (e) {
  e.preventDefault();
  document.getElementById("aviso-enviado").classList.remove("oculto");
  e.target.querySelector("button").disabled = true;
});
