// Nordestinando - tema claro/escuro. Carregue no <head> para não piscar.
// A escolha fica no navegador (localStorage) e também na conta (servidor), quando há login.
(function () {
  function aplicar(tema) {
    if (tema === "claro" || tema === "escuro") document.documentElement.setAttribute("data-tema", tema);
    else document.documentElement.removeAttribute("data-tema");
  }
  window.aplicarTema = function (tema) {
    aplicar(tema);
    try { localStorage.setItem("tema", tema); } catch (e) {}
  };
  try { aplicar(localStorage.getItem("tema")); } catch (e) {}
})();
