// Recuperar senha - Nordestinando
// Tela visual: ainda não envia email de verdade

document.getElementById("form-recuperar").addEventListener("submit", function (e) {
  e.preventDefault();
  document.getElementById("aviso-enviado").classList.remove("oculto");
  e.target.querySelector("button").disabled = true;
});
