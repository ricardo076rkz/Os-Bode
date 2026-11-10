// Páginas de Termos e Política: preenche versão, controlador e contato vindos do servidor
pegarId("voltar").addEventListener("click", function (e) {
  e.preventDefault();
  if (document.referrer && history.length > 1) history.back();
  else window.location.href = "tela.html";
});
api("GET", "/api/lgpd/info").then(function (d) {
  const termos = location.pathname.indexOf("termos") >= 0;
  pegarId("versao").textContent = termos ? d.versao_termos : d.versao_privacidade;
  const c = pegarId("controlador");
  if (c) c.textContent = d.controlador;
  const ct = pegarId("contato");
  if (ct) {
    if (d.contato) {
      const a = criar("a", "", d.contato);
      a.href = "mailto:" + d.contato;
      ct.textContent = "";
      ct.appendChild(a);
    } else {
      ct.textContent = "o e-mail do encarregado (ainda não informado pelo operador deste servidor)";
    }
  }
  [["ret-atividade", "atividade"], ["ret-sessao", "sessao_inativa"], ["ret-notif", "notificacao_lida"]].forEach(function (p) {
    const el = pegarId(p[0]);
    if (el) el.textContent = d.retencao_dias[p[1]];
  });
}, function () {});
