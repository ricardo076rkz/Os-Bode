// Redefinir senha pelo link recebido (…?token=...) - Nordestinando
const token = new URLSearchParams(window.location.search).get("token") || "";
const form = pegarId("form");
const msg = pegarId("mensagem");

if (!token) {
  form.querySelectorAll("input,button").forEach(function (c) { c.disabled = true; });
  mostrarMensagem(msg, "Link incompleto. Peça um novo em “Esqueci minha senha”.", "erro");
}

form.addEventListener("submit", async function (e) {
  e.preventDefault();
  const botao = form.querySelector("button");
  mostrarErrosCampos(form, {});
  botao.disabled = true;
  try {
    await api("POST", "/api/senha/redefinir", { token: token, senha: form.senha.value, confirmar_senha: form.confirmar_senha.value });
    mostrarMensagem(msg, "Senha alterada! Indo para o login...", "ok");
    setTimeout(function () { window.location.href = "tela.html"; }, 1500);
  } catch (erro) {
    mostrarErrosCampos(form, erro.campos || {});
    mostrarMensagem(msg, erro.erro, "erro");
    botao.disabled = false;
  }
});
