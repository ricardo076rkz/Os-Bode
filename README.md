# Nordestinando

Guia de cidade (Caruaru) com área do comerciante. Front em HTML/CSS/JS, servidor em Flask, banco SQLite.

## Como rodar

1. Instale o Python 3.10+ e as dependências:
   ```
   pip install -r python/requirements.txt
   ```
2. Copie `.env.exemplo` para `.env` (não precisa preencher nada).
3. Inicie o servidor:
   ```
   python python/app.py
   ```
4. Abra **http://localhost:5000** (não abra os .html clicando neles: o login e o banco só funcionam pelo servidor).

O banco (`python/nordestinando.db`) é criado sozinho na primeira execução.

## Telas

- `index.html` – início
- `html/explorar.html` – mapa, lojas, eventos (usuário pode avaliar e reservar)
- `html/tela.html` – entrar / criar conta, escolhendo **Sou usuário** ou **Sou comerciante**
- `html/comerciante.html` – login do comerciante
- `html/cadastrar_estabelecimento.html` – cadastro do comerciante em 4 etapas
- `html/minha_loja.html` – painel (vitrine, eventos, avaliações, estatísticas, dados e localização)

## Perfis e permissões

| Ação | Usuário (CLIENTE) | Comerciante (LOGISTA) |
|---|---|---|
| Ver lojas, eventos e mapa | sim | sim |
| Avaliar loja / reservar item | sim | não |
| Painel "Minha loja" | não | sim (só da própria loja) |

## Mapa (gratuito)

O mapa usa **OpenStreetMap + Leaflet**: não precisa de chave, cadastro nem cartão.
- Imagens do mapa: OpenStreetMap
- Endereço -> coordenadas: Nominatim (busca do OpenStreetMap; uso leve, máximo 1 consulta por segundo)
- CEP -> endereço: ViaCEP
- "Como chegar": abre o Google Maps com a rota (é só um link, grátis)
- Clima de Caruaru no Explorar: Open-Meteo (gratuito, sem chave)

O navegador precisa de internet para carregar o mapa. Sem internet, o resto do sistema funciona e o mapa mostra um aviso.

## Banco

Esquema em `python/schema.sql` (mesmas tabelas do `sql/banco.sql`, ampliadas). A pasta `python/Models` e
`python/Repository` (versão antiga com SQLAlchemy/PostgreSQL) não é usada pelo servidor atual.
