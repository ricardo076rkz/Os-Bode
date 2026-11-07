// Nordestinando - dados e funções usados por mais de uma tela

// ---------- dados de exemplo (depois vem do banco) ----------
const dadosLoja = { nome: "Pastelaria", endereco: "Rua Blablabla, nº 10" };

const avaliacoes = [
  { cliente: "Maria S.", nota: 5, comentario: "Pastel crocante e atendimento excelente!", data: "2026-10-28" },
  { cliente: "João P.", nota: 4, comentario: "Muito bom, só demorou um pouco no sábado.", data: "2026-10-30" },
  { cliente: "Ana L.", nota: 5, comentario: "Recomendo, voltarei mais vezes.", data: "2026-11-02" },
  { cliente: "Carlos M.", nota: 3, comentario: "Bom sabor, mas o caldo de cana estava morno.", data: "2026-11-03" },
  { cliente: "Beatriz R.", nota: 5, comentario: "Preço justo e porção generosa.", data: "2026-11-05" }
];

const vitrinePadrao = [
  { id: 1, nome: "Pastel de carne", valor: 8.5, foto: "../js/img/pastel-carne.jpg" },
  { id: 2, nome: "Pastel de queijo", valor: 7, foto: "../js/img/pastel-queijo.jpg" },
  { id: 3, nome: "Caldo de cana", valor: 6, foto: "../js/img/caldo-de-cana.jpg" }
];

// ---------- funções pequenas ----------

// lê do localStorage (se não tiver nada, devolve o valor padrão)
function pegar(chave, padrao) {
  try {
    const texto = localStorage.getItem(chave);
    if (texto) {
      return JSON.parse(texto);
    }
  } catch (erro) {
    // se der erro, usa o padrão
  }
  return padrao;
}

function guardar(chave, dados) {
  try {
    localStorage.setItem(chave, JSON.stringify(dados));
  } catch (erro) {
    alert("Não deu para salvar. Tente uma foto menor.");
  }
}

function pegarId(id) {
  return document.getElementById(id);
}

function criar(tag, classe, texto) {
  const elemento = document.createElement(tag);
  if (classe) elemento.className = classe;
  if (texto !== undefined) elemento.textContent = texto;
  return elemento;
}

function dinheiro(valor) {
  return "R$ " + valor.toFixed(2).replace(".", ",");
}

function dataBR(texto) {
  const partes = texto.split("-");
  return partes[2] + "/" + partes[1] + "/" + partes[0];
}

function estrelas(nota) {
  return "★".repeat(nota) + "☆".repeat(5 - nota);
}

function notaFormatada(n) {
  return n.toFixed(1).replace(".", ",");
}

function mediaNotas() {
  let soma = 0;
  avaliacoes.forEach(function (a) {
    soma += a.nota;
  });
  return soma / avaliacoes.length;
}