// Modo de teste: qualquer usuário e senha entram (só existe na branch teste-por-cima)
// Depende de api.js

api("GET", "/api/config").then(function (config) {
  if (!config.modo_teste) return;

  // e-mail vira texto livre
  document.querySelectorAll('#form-login input[type="email"]').forEach(function (campo) {
    campo.type = "text";
    campo.placeholder = "qualquer usuário";
    campo.removeAttribute("autocomplete");
  });

  const aviso = document.createElement("p");
  aviso.className = "mensagem info";
  aviso.textContent = "Modo de teste: digite qualquer usuário e qualquer senha. A conta é criada na hora.";
  const form = document.getElementById("form-login");
  form.parentNode.insertBefore(aviso, form);
}, function () {});
