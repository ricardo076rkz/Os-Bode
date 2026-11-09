// Recuperar senha - Nordestinando: pede um link ao servidor (e-mail se o SMTP estiver configurado)
const form = document.getElementById("form-recuperar");
const aviso = document.getElementById("aviso-enviado");

form.addEventListener("submit", async function (e) {
  e.preventDefault();
  const botao = form.querySelector("button");
  mostrarErrosCampos(form, {});
  botao.disabled = true;
  try {
    const r = await api("POST", "/api/senha/esqueci", { email: form.email.value });
    let texto = "Se esse e-mail tiver cadastro, enviamos um link para criar uma nova senha. Ele vale por 1 hora.";
    if (r.entrega == "console") texto += " (Este servidor ainda não tem e-mail configurado: o link aparece no terminal onde o servidor está rodando.)";
    mostrarMensagem(aviso, texto, "ok");
  } catch (erro) {
    mostrarErrosCampos(form, erro.campos || {});
    mostrarMensagem(aviso, erro.erro, "erro");
    botao.disabled = false;
  }
});
