// Cadastrar estabelecimento - Nordestinando
// Tela visual: ainda não grava no banco

const cnpj = document.getElementById("cnpj");

// Máscara do CNPJ: 00.000.000/0000-00
cnpj.addEventListener("input", () => {
  let n = cnpj.value.replace(/\D/g, "").slice(0, 14);
  n = n.replace(/^(\d{2})(\d)/, "$1.$2");
  n = n.replace(/^(\d{2})\.(\d{3})(\d)/, "$1.$2.$3");
  n = n.replace(/\.(\d{3})(\d)/, ".$1/$2");
  n = n.replace(/(\d{4})(\d)/, "$1-$2");
  cnpj.value = n;
});

// Preenche latitude e longitude com a localização atual
document.getElementById("btn-local").addEventListener("click", () => {
  if (!navigator.geolocation) {
    alert("Seu navegador não tem localização.");
    return;
  }
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      document.getElementById("latitude").value = pos.coords.latitude.toFixed(6);
      document.getElementById("longitude").value = pos.coords.longitude.toFixed(6);
    },
    () => alert("Não foi possível pegar a localização.")
  );
});

document.getElementById("form-cadastro").addEventListener("submit", (e) => {
  e.preventDefault();
  alert("Estabelecimento cadastrado! Agora faça o login.");
  window.location.href = "comerciante.html";
});