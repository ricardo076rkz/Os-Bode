// Nordestinando - funções pequenas usadas por mais de uma tela

function pegarId(id) {
  return document.getElementById(id);
}

function criar(tag, classe, texto) {
  const elemento = document.createElement(tag);
  if (classe) elemento.className = classe;
  if (texto !== undefined && texto !== null) elemento.textContent = texto;
  return elemento;
}

function dinheiro(valor) {
  return "R$ " + Number(valor).toFixed(2).replace(".", ",");
}

// "2026-11-07" ou "2026-11-07 20:10:00" -> "07/11/2026"
function dataBR(texto) {
  const partes = String(texto).slice(0, 10).split("-");
  return partes[2] + "/" + partes[1] + "/" + partes[0];
}

function estrelas(nota) {
  return "★".repeat(nota) + "☆".repeat(5 - nota);
}

// nota pode ser null (loja ainda sem avaliações)
function notaFormatada(n) {
  if (n === null || n === undefined) return "—";
  return Number(n).toFixed(1).replace(".", ",");
}

// só números -> (81) 99999-9999
function telefoneBR(numeros) {
  const n = String(numeros || "").replace(/\D/g, "");
  if (n.length == 11) return "(" + n.slice(0, 2) + ") " + n.slice(2, 7) + "-" + n.slice(7);
  if (n.length == 10) return "(" + n.slice(0, 2) + ") " + n.slice(2, 6) + "-" + n.slice(6);
  return numeros || "";
}

// máscaras de digitação
function mascaraTelefone(input) {
  input.addEventListener("input", function () {
    input.value = telefoneBR(input.value.replace(/\D/g, "").slice(0, 11));
  });
}

function mascaraCNPJ(input) {
  input.addEventListener("input", function () {
    const n = input.value.replace(/\D/g, "").slice(0, 14);
    let t = n;
    if (n.length > 12) t = n.slice(0, 2) + "." + n.slice(2, 5) + "." + n.slice(5, 8) + "/" + n.slice(8, 12) + "-" + n.slice(12);
    else if (n.length > 8) t = n.slice(0, 2) + "." + n.slice(2, 5) + "." + n.slice(5, 8) + "/" + n.slice(8);
    else if (n.length > 5) t = n.slice(0, 2) + "." + n.slice(2, 5) + "." + n.slice(5);
    else if (n.length > 2) t = n.slice(0, 2) + "." + n.slice(2);
    input.value = t;
  });
}

function mascaraCEP(input) {
  input.addEventListener("input", function () {
    const n = input.value.replace(/\D/g, "").slice(0, 8);
    input.value = n.length > 5 ? n.slice(0, 5) + "-" + n.slice(5) : n;
  });
}

// tabela de horários de funcionamento (usada no cadastro e na edição da loja)
const NOMES_DIAS = { seg: "Segunda", ter: "Terça", qua: "Quarta", qui: "Quinta", sex: "Sexta", sab: "Sábado", dom: "Domingo" };

function montarHorarios(container, horarios) {
  container.innerHTML = "";
  Object.keys(NOMES_DIAS).forEach(function (dia) {
    const h = (horarios && horarios[dia]) || { fechado: dia == "dom", abre: "08:00", fecha: "18:00" };
    const linha = criar("div", "horario-linha");
    linha.dataset.dia = dia;
    linha.appendChild(criar("span", "horario-dia", NOMES_DIAS[dia]));

    const abre = document.createElement("input");
    abre.type = "time";
    abre.className = "h-abre";
    abre.value = h.abre || "08:00";
    const fecha = document.createElement("input");
    fecha.type = "time";
    fecha.className = "h-fecha";
    fecha.value = h.fecha || "18:00";

    const rotulo = criar("label", "horario-fechado");
    const check = document.createElement("input");
    check.type = "checkbox";
    check.className = "h-fechado";
    check.checked = !!h.fechado;
    rotulo.appendChild(check);
    rotulo.appendChild(document.createTextNode(" Fechado"));

    function atualizar() {
      abre.disabled = fecha.disabled = check.checked;
    }
    check.addEventListener("change", atualizar);
    atualizar();

    linha.appendChild(abre);
    linha.appendChild(fecha);
    linha.appendChild(rotulo);
    container.appendChild(linha);
  });
}

function lerHorarios(container) {
  const saida = {};
  container.querySelectorAll(".horario-linha").forEach(function (linha) {
    saida[linha.dataset.dia] = {
      fechado: linha.querySelector(".h-fechado").checked,
      abre: linha.querySelector(".h-abre").value,
      fecha: linha.querySelector(".h-fecha").value
    };
  });
  return saida;
}

// resumo curto para o mapa/lista: "Hoje: 08:00–18:00" ou "Hoje: fechado"
function horarioHoje(horarios) {
  const dias = ["dom", "seg", "ter", "qua", "qui", "sex", "sab"];
  const h = horarios && horarios[dias[new Date().getDay()]];
  if (!h) return "";
  return h.fechado ? "Hoje: fechado" : "Hoje: " + h.abre + "–" + h.fecha;
}
