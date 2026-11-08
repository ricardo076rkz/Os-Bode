// Nordestinando - mapa gratuito (OpenStreetMap + Leaflet). Não precisa de chave nem de cartão.
//  - mapa: Leaflet (biblioteca) com as imagens do OpenStreetMap
//  - endereço -> coordenadas: Nominatim (busca do OpenStreetMap)
//  - CEP -> endereço: ViaCEP
// Depende de comum.js

const LEAFLET_VERSAO = "1.9.4";
let promessaLeaflet = null;

// baixa o Leaflet (css + js) uma única vez
function carregarLeaflet() {
  if (promessaLeaflet) return promessaLeaflet;

  promessaLeaflet = new Promise(function (resolve, reject) {
    if (window.L) {
      resolve(window.L);
      return;
    }
    const base = "https://unpkg.com/leaflet@" + LEAFLET_VERSAO + "/dist/";
    const css = document.createElement("link");
    css.rel = "stylesheet";
    css.href = base + "leaflet.css";
    document.head.appendChild(css);

    const script = document.createElement("script");
    script.src = base + "leaflet.js";
    script.onload = function () {
      resolve(window.L);
    };
    script.onerror = function () {
      promessaLeaflet = null;
      reject(new Error("SEM_REDE"));
    };
    document.head.appendChild(script);
  });
  return promessaLeaflet;
}

function textoErroMaps(erro) {
  if (erro && erro.message == "SEM_REDE") {
    return "Não foi possível carregar o mapa (sem internet?).";
  }
  return "Não foi possível carregar o mapa.";
}

// desenha um mapa dentro do elemento; se não der, escreve o motivo no lugar do mapa
function criarMapa(elemento, centro, zoom) {
  return carregarLeaflet().then(
    function (L) {
      elemento.classList.remove("mapa-erro");
      const mapa = L.map(elemento).setView([centro.lat, centro.lng], zoom);
      L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; contribuidores do <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a>"
      }).addTo(mapa);
      return mapa;
    },
    function (erro) {
      elemento.classList.add("mapa-erro");
      elemento.textContent = textoErroMaps(erro);
      throw erro;
    }
  );
}

// centro padrão: Caruaru
const CARUARU = { lat: -8.2829, lng: -35.9761 };

// link "Como chegar": abre o Google Maps já com a rota (é só um link, não precisa de chave)
function linkRota(lat, lng) {
  return "https://www.google.com/maps/dir/?api=1&destination=" + lat + "," + lng;
}

// endereço escrito -> {lat, lng} (ou null se não achar)
async function buscarEndereco(texto) {
  const url = "https://nominatim.openstreetmap.org/search?format=json&limit=1&countrycodes=br&q=" + encodeURIComponent(texto);
  const resposta = await fetch(url, { headers: { Accept: "application/json" } });
  if (!resposta.ok) throw new Error("FALHA_BUSCA");
  const lista = await resposta.json();
  if (!lista.length) return null;
  return { lat: parseFloat(lista[0].lat), lng: parseFloat(lista[0].lon) };
}

// ---------- localização da loja: CEP -> endereço -> coordenadas -> marcador ----------
// c = {cep, rua, numero, bairro, cidade, estado, lat, lng, botao, mapa, aviso} (elementos do formulário)
function iniciarLocalizacao(c) {
  let mapa = null;
  let marcador = null;

  function aviso(texto, tipo) {
    mostrarMensagem(c.aviso, texto, tipo || "info");
  }

  function colocarMarcador(lat, lng) {
    c.lat.value = Number(lat).toFixed(6);
    c.lng.value = Number(lng).toFixed(6);
    if (!mapa) return;
    const posicao = [Number(lat), Number(lng)];
    if (!marcador) {
      marcador = L.marker(posicao, { draggable: true }).addTo(mapa);
      marcador.on("dragend", function () {
        const p = marcador.getLatLng();
        c.lat.value = p.lat.toFixed(6);
        c.lng.value = p.lng.toFixed(6);
      });
    } else {
      marcador.setLatLng(posicao);
    }
    mapa.setView(posicao, 17);
  }

  const temPonto = c.lat.value && c.lng.value;
  criarMapa(c.mapa, temPonto ? { lat: Number(c.lat.value), lng: Number(c.lng.value) } : CARUARU, temPonto ? 17 : 14).then(
    function (m) {
      mapa = m;
      // clicar no mapa também marca o ponto
      m.on("click", function (e) {
        colocarMarcador(e.latlng.lat, e.latlng.lng);
        aviso("Ponto marcado no mapa. Arraste o marcador para ajustar.", "ok");
      });
      if (temPonto) colocarMarcador(c.lat.value, c.lng.value);
    },
    function (erro) {
      aviso(textoErroMaps(erro) + " Você ainda pode digitar latitude e longitude.", "erro");
    }
  );

  // CEP preenche o endereço (ViaCEP, serviço gratuito)
  c.cep.addEventListener("blur", function () {
    const cep = c.cep.value.replace(/\D/g, "");
    if (cep.length != 8) return;
    fetch("https://viacep.com.br/ws/" + cep + "/json/")
      .then(function (r) {
        return r.json();
      })
      .then(function (d) {
        if (d.erro) {
          aviso("CEP não encontrado.", "erro");
          return;
        }
        c.rua.value = d.logradouro || c.rua.value;
        c.bairro.value = d.bairro || c.bairro.value;
        c.cidade.value = d.localidade || c.cidade.value;
        c.estado.value = d.uf || c.estado.value;
        aviso("Endereço preenchido pelo CEP. Agora clique em “Localizar no mapa”.", "ok");
      })
      .catch(function () {
        aviso("Não consegui consultar o CEP agora. Preencha o endereço à mão.", "erro");
      });
  });

  // endereço -> coordenadas
  c.botao.addEventListener("click", async function () {
    if (!c.rua.value || !c.cidade.value) {
      aviso("Preencha ao menos rua e cidade.", "erro");
      return;
    }
    aviso("Procurando o endereço...", "info");
    const completo = [c.rua.value + " " + c.numero.value, c.bairro.value, c.cidade.value, c.estado.value, "Brasil"].join(", ");
    const semNumero = [c.rua.value, c.cidade.value, c.estado.value, "Brasil"].join(", ");
    try {
      // se não achar com o número, tenta só a rua
      const ponto = (await buscarEndereco(completo)) || (await buscarEndereco(semNumero));
      if (!ponto) {
        aviso("Não encontrei esse endereço. Marque o ponto clicando no mapa.", "erro");
        return;
      }
      colocarMarcador(ponto.lat, ponto.lng);
      aviso("Local encontrado. Confira no mapa e arraste o marcador se precisar.", "ok");
    } catch (erro) {
      aviso("A busca de endereço não respondeu. Marque o ponto clicando no mapa.", "erro");
    }
  });

  // quem digita latitude/longitude à mão também move o marcador
  [c.lat, c.lng].forEach(function (campo) {
    campo.addEventListener("change", function () {
      if (c.lat.value !== "" && c.lng.value !== "" && mapa) colocarMarcador(c.lat.value, c.lng.value);
    });
  });

  return {
    definir: function (lat, lng) {
      c.lat.value = lat;
      c.lng.value = lng;
      if (mapa) colocarMarcador(lat, lng);
    },
    reajustar: function () {
      if (mapa) mapa.invalidateSize();
    }
  };
}
