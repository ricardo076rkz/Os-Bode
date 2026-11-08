// Nordestinando - Google Maps
// A chave vem do servidor (arquivo .env -> GOOGLE_MAPS_API_KEY). Nada de chave no código.
// Depende de api.js

let promessaMaps = null;

function carregarMaps() {
  if (promessaMaps) return promessaMaps;

  promessaMaps = api("GET", "/api/config").then(function (config) {
    if (!config.maps_key) {
      throw new Error("SEM_CHAVE");
    }
    return new Promise(function (resolve, reject) {
      window.__mapsPronto = function () {
        resolve(window.google.maps);
      };
      // o Google chama essa função quando a chave é recusada
      window.gm_authFailure = function () {
        reject(new Error("CHAVE_RECUSADA"));
      };
      const script = document.createElement("script");
      script.src =
        "https://maps.googleapis.com/maps/api/js?key=" + encodeURIComponent(config.maps_key) +
        "&callback=__mapsPronto&loading=async";
      script.async = true;
      script.onerror = function () {
        reject(new Error("SEM_REDE"));
      };
      document.head.appendChild(script);
    });
  });
  return promessaMaps;
}

function textoErroMaps(erro) {
  const mensagens = {
    SEM_CHAVE: "Mapa desativado: falta a chave GOOGLE_MAPS_API_KEY no arquivo .env do servidor.",
    CHAVE_RECUSADA: "O Google recusou a chave do mapa. Confira se a Maps JavaScript API e a Geocoding API estão ativadas e se o domínio localhost está liberado na chave.",
    SEM_REDE: "Não foi possível carregar o Google Maps (sem internet?)."
  };
  return mensagens[erro.message] || "Não foi possível carregar o mapa.";
}

// desenha um mapa dentro do elemento; se não der, escreve o motivo no lugar do mapa
function criarMapa(elemento, centro, zoom) {
  return carregarMaps().then(
    function (maps) {
      elemento.classList.remove("mapa-erro");
      return new maps.Map(elemento, {
        center: centro,
        zoom: zoom,
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: false
      });
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

// link "Como chegar" (abre o Google Maps com a rota até a loja; não precisa de chave)
function linkRota(lat, lng) {
  return "https://www.google.com/maps/dir/?api=1&destination=" + lat + "," + lng;
}

// ---------- localização da loja: CEP -> endereço -> coordenadas -> marcador ----------
// campos: {cep, rua, numero, bairro, cidade, estado, lat, lng, botao, mapa, aviso} (elementos do formulário)
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
    const posicao = { lat: Number(lat), lng: Number(lng) };
    if (!marcador) {
      marcador = new google.maps.Marker({ map: mapa, position: posicao, draggable: true });
      marcador.addListener("dragend", function () {
        const p = marcador.getPosition();
        c.lat.value = p.lat().toFixed(6);
        c.lng.value = p.lng().toFixed(6);
      });
    } else {
      marcador.setPosition(posicao);
    }
    mapa.setCenter(posicao);
    mapa.setZoom(17);
  }

  // mapa: clicar também marca o ponto
  const temPonto = c.lat.value && c.lng.value;
  criarMapa(c.mapa, temPonto ? { lat: Number(c.lat.value), lng: Number(c.lng.value) } : CARUARU, temPonto ? 17 : 14).then(
    function (m) {
      mapa = m;
      m.addListener("click", function (e) {
        colocarMarcador(e.latLng.lat(), e.latLng.lng());
        aviso("Ponto marcado no mapa. Arraste o marcador para ajustar.", "ok");
      });
      if (temPonto) colocarMarcador(c.lat.value, c.lng.value);
    },
    function (erro) {
      aviso(textoErroMaps(erro) + " Você ainda pode digitar latitude e longitude.", "erro");
    }
  );

  // CEP preenche o endereço (ViaCEP, serviço gratuito dos Correios)
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

  // endereço -> coordenadas (Geocoding)
  c.botao.addEventListener("click", function () {
    if (!c.rua.value || !c.cidade.value) {
      aviso("Preencha ao menos rua e cidade.", "erro");
      return;
    }
    const endereco = [c.rua.value + " " + c.numero.value, c.bairro.value, c.cidade.value, c.estado.value, "Brasil"].join(", ");
    carregarMaps().then(
      function (maps) {
        new maps.Geocoder().geocode({ address: endereco, region: "BR" }).then(
          function (resposta) {
            const p = resposta.results[0].geometry.location;
            colocarMarcador(p.lat(), p.lng());
            aviso("Local encontrado. Confira no mapa e arraste o marcador se precisar.", "ok");
          },
          function () {
            aviso("Não encontrei esse endereço. Marque o ponto clicando no mapa.", "erro");
          }
        );
      },
      function (erro) {
        aviso(textoErroMaps(erro), "erro");
      }
    );
  });

  // quem digita latitude/longitude à mão também move o marcador
  [c.lat, c.lng].forEach(function (campo) {
    campo.addEventListener("change", function () {
      if (c.lat.value !== "" && c.lng.value !== "" && mapa) colocarMarcador(c.lat.value, c.lng.value);
    });
  });

  return {
    // para quem edita: mostra o ponto que já estava salvo
    definir: function (lat, lng) {
      c.lat.value = lat;
      c.lng.value = lng;
      if (mapa) colocarMarcador(lat, lng);
    },
    reajustar: function () {
      if (mapa) google.maps.event.trigger(mapa, "resize");
    }
  };
}
