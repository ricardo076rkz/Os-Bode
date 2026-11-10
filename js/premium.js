// Nordestinando+ - estado do plano, assinatura e cancelamento
const msg = pegarId("mensagem");
const ROTULOS = {
  gratuito: "Plano gratuito",
  premium_ativo: "Nordestinando+ ativo",
  premium_cancelado: "Nordestinando+ cancelado",
  premium_expirado: "Nordestinando+ expirado",
};

function linha(rotulo, valor) {
  const l = criar("div", "dado-linha");
  l.appendChild(criar("span", "", rotulo));
  l.appendChild(criar("span", "", valor));
  return l;
}

async function carregar() {
  const d = await api("GET", "/api/premium");
  const p = d.plano;
  pegarId("preco").textContent = p.preco.replace(".", ",");
  const caixa = pegarId("estado-plano");
  caixa.innerHTML = "";
  caixa.appendChild(linha("Seu plano", ROTULOS[p.estado]));
  caixa.appendChild(linha("Multiplicador de pontos", p.multiplicador + "x"));
  if (p.fim) caixa.appendChild(linha(p.estado == "premium_ativo" ? "Válido até" : "Terminou em", dataBR(p.fim)));
  if (p.ambiente == "demo") caixa.appendChild(linha("Pagamento", "Demonstração, sem cobrança real"));

  const acoes = pegarId("acoes");
  acoes.innerHTML = "";
  if (p.estado == "premium_ativo") {
    const cancelar = criar("button", "botao contorno", "Cancelar assinatura");
    cancelar.type = "button";
    cancelar.addEventListener("click", async function () {
      if (!confirm("Cancelar o Nordestinando+? Seus pontos continuam, mas voltam a valer 1x.")) return;
      try {
        await api("POST", "/api/premium/cancelar");
        mostrarMensagem(msg, "Assinatura cancelada.", "ok");
        carregar();
      } catch (e) { mostrarMensagem(msg, e.erro, "erro"); }
    });
    acoes.appendChild(cancelar);
  } else {
    const assinar = criar("button", "botao", (p.estado == "gratuito" ? "Assinar por " : "Assinar de novo por ") + p.preco.replace(".", ",") + "/mês");
    assinar.type = "button";
    assinar.addEventListener("click", async function () {
      assinar.disabled = true;
      try {
        await api("POST", "/api/premium/assinar");
        mostrarMensagem(msg, "Nordestinando+ ativado (demonstração, sem cobrança real).", "ok");
        carregar();
      } catch (e) {
        mostrarMensagem(msg, e.erro, "erro");
        assinar.disabled = false;
      }
    });
    acoes.appendChild(assinar);
  }
  const aviso = pegarId("aviso");
  if (p.demo_disponivel) aviso.textContent = "MODO DEMONSTRAÇÃO: o pagamento é simulado e nenhum valor é cobrado. A cobrança real depende de integrar um meio de pagamento (Pix ou cartão) no servidor.";
  else if (!p.pagamento_configurado) aviso.textContent = "O pagamento ainda não foi configurado neste servidor, então a assinatura não pode ser ativada por aqui.";
  else aviso.textContent = "";
}

pegarId("exemplo").textContent = "Exemplo: uma avaliação completa de 40 pontos rende 80 com o Nordestinando+.";
carregar().catch(function (e) {
  pegarId("estado-plano").appendChild(criar("p", "", e.status == 401 || e.status == 403 ? "Entre como usuário para ver o plano." : "Não foi possível carregar."));
});
