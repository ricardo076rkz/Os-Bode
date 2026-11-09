# Nordestinando

Guia de cidade (Caruaru) com área do comerciante. Front em HTML/CSS/JS, servidor em Flask (Python) e banco SQLite.

- **Usuário:** vê lojas, eventos, mapa e o clima; avalia lojas e reserva itens.
- **Comerciante:** cadastra a loja em 4 etapas e gerencia vitrine, eventos, avaliações, estatísticas e localização.

---

## 1. Rodar pela primeira vez (passo a passo do zero)

### O que instalar (uma vez só)

| Programa | Para quê | Onde baixar | Conferir |
|---|---|---|---|
| Git | baixar o projeto | https://git-scm.com/downloads | `git --version` |
| Python 3.10 ou mais novo | rodar o servidor | https://www.python.org/downloads (no Windows, marque **"Add python.exe to PATH"**) | `python --version` |
| VS Code | editar | https://code.visualstudio.com | |

### Baixar o projeto

```
git clone https://github.com/ricardo076rkz/Os-Bode.git
cd Os-Bode
git checkout front-unificado
```

> Depois que a branch `front-unificado` for juntada à `main`, o `git checkout` não é mais necessário.

### Instalar e ligar

```
python -m pip install -r python/requirements.txt
python python/app.py
```

- No **Windows**, se `python` não for reconhecido, use `py` no lugar (`py -m pip ...` e `py python/app.py`).
- No **Mac/Linux**, use `python3` e `python3 -m pip`.
- Deve aparecer `Running on http://127.0.0.1:5000`. **Deixe esse terminal aberto**: fechar desliga o servidor.

### Abrir o app

Acesse **http://localhost:5000** no navegador.

Não abra os `.html` clicando neles e não use o Live Server: sem o servidor o login e o banco não funcionam (aparece "Resposta inesperada do servidor").

### Arquivo `.env` (opcional)

Copie `.env.exemplo` para `.env`. Não precisa preencher nada: o mapa e o clima não usam chave. O `.env` nunca vai para o GitHub.

---

## 2. No dia a dia

| Quero... | Comando |
|---|---|
| Pegar as novidades do grupo | `git pull` |
| Ligar o servidor | `python python/app.py` |
| Desligar o servidor | **Ctrl+C** no terminal |
| Mudar a porta (se a 5000 estiver ocupada) | PowerShell: `$env:PORT=5001` e depois ligar. Mac/Linux: `PORT=5001 python3 python/app.py` |
| Ver o visual antigo/novo atualizado | **Ctrl+F5** no navegador |
| Começar com o banco zerado | desligue o servidor e apague `python/nordestinando.db` |

### Importante: o banco é local

O banco é um arquivo (`python/nordestinando.db`) **na máquina de cada pessoa**. Contas e lojas criadas no seu computador **não aparecem** no computador do colega. Para a apresentação, escolham **um computador** para ligar o servidor e criem as contas e lojas nele. Se quiserem que outros aparelhos da mesma rede Wi-Fi acessem, abram `http://IP-DO-COMPUTADOR:5000` (o servidor já aceita conexões da rede).

---

## 3. Telas

| Tela | Arquivo | Para quê |
|---|---|---|
| Início | `index.html` | Explorar Cidade, Sou Comerciante ou conta de usuário |
| Entrar | `html/tela.html` | Escolher "Sou usuário" ou "Sou comerciante"; entrar ou criar conta de usuário |
| Login do comerciante | `html/comerciante.html` | Entrar na área da loja |
| Cadastro da loja | `html/cadastrar_estabelecimento.html` | 4 etapas: seus dados, estabelecimento, endereço e localização, horários |
| Minha loja | `html/minha_loja.html` | Painel do comerciante |
| Explorar | `html/explorar.html` | Mapa, clima, lojas e eventos |
| Recuperar senha | `html/recuperar_senha.html` | Pede o link de nova senha (por e-mail, se o SMTP estiver no `.env`) |
| Nova senha | `html/redefinir_senha.html` | Abre pelo link recebido (`?token=...`, vale 1 hora, uso único) |
| Meu perfil | `html/perfil.html` | Foto, dados, trocar senha, histórico de atividades, sair |
| Notificações | `html/notificacoes.html` | Central: não lidas, marcar lida, marcar todas, excluir, apagar lidas |
| Configurações | `html/configuracoes.html` | Tema claro/escuro, notificações por categoria, privacidade, aparelhos conectados, excluir conta |

## 4. Perfis e permissões

O servidor confere o perfil em toda ação.

| Ação | Usuário | Comerciante |
|---|---|---|
| Ver lojas, eventos, mapa e clima | sim | sim |
| Avaliar loja (1 por loja, pode mudar) | sim | não |
| Reservar item da vitrine | sim | não |
| Painel "Minha loja" | não | sim, só da própria loja |
| Entrar pela opção errada (usuário como comerciante) | recusado | recusado |
| Perfil, notificações, configurações (só os próprios) | sim | sim |

**Conta e segurança:** as sessões ficam no banco (dá para desconectar aparelhos); trocar ou redefinir a senha derruba os outros aparelhos; 5 senhas erradas em 10 minutos bloqueiam o login por um tempo; o link de nova senha guarda só o hash do token; excluir a conta pede a senha e a palavra EXCLUIR e apaga tudo ligado a ela.

**Notificações** são geradas por ações reais: nova avaliação e novo pedido (para o comerciante), pedido registrado e novo evento de loja já visitada (para o usuário), troca de senha ou e-mail (segurança, sempre ligada). Cada pessoa liga e desliga as categorias em Configurações. O sino confere novidades a cada 30 segundos (não é tempo real por WebSocket).

### Recuperar senha por e-mail
No `.env`, preencha `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` e `APP_URL` (veja `.env.exemplo`). Sem isso, o link de nova senha é impresso no terminal onde o servidor roda (serve para testar).

### Testes automáticos
```
python tests/teste_api.py          # cadastro, login, permissões, loja, vitrine
python tests/teste_conta_api.py    # perfil, senha, sessões, notificações, recuperação, exclusão
```
Cada um usa um banco temporário e imprime `FALHAS: 0` / `OK n FALHAS 0` quando passa.

## 5. APIs gratuitas (nenhuma precisa de chave)

| Serviço | Para quê |
|---|---|
| OpenStreetMap + Leaflet | Mapa com marcadores e balão da loja |
| Nominatim | Endereço vira latitude e longitude |
| ViaCEP | CEP preenche o endereço |
| Open-Meteo | Clima de Caruaru |
| Link do Google Maps | Botão "Como chegar" abre a rota (é só um link) |

O navegador precisa de internet para essas consultas. Se uma falhar, o resto continua funcionando e a tela avisa.

## 6. Onde fica cada coisa

| Onde | O que tem |
|---|---|
| `python/app.py` | Rotas da API, validações, login e permissões |
| `python/schema.sql` | Tabelas: usuario, logista, loja, item_vitrine, avaliacao, pedido, evento |
| `python/banco.py` | Conexão com o banco |
| `python/requirements.txt` | Dependências do Python (Flask e python-dotenv) |
| `js/api.js` | Conversa com o servidor e mostra erros nos campos |
| `js/mapa.js` | Mapa, CEP e busca de endereço |
| `js/icones.js` | Ícones SVG |
| `js/comum.js` | Máscaras, horários, "aberto agora" e funções pequenas |
| `js/*.js` (demais) | Um script por tela |
| `style/style.css`, `style/loja.css` | Visual: barro (vermelho do logo), sol, mata e papel, com as bandeirinhas de São João |
| `sql/banco.sql` | Modelagem original do grupo (referência) |
| `python/Models`, `python/Repository` | Versão antiga com SQLAlchemy/PostgreSQL, **não usada** |

Segurança: senhas guardadas com hash; sessão por cookie assinado; só as pastas do site são entregues pelo servidor (o código Python e o banco não); `.env` e `*.db` ficam fora do GitHub.

---

## 7. Problemas comuns

| O que aparece | Causa | O que fazer |
|---|---|---|
| `ERR_CONNECTION_REFUSED` em localhost:5000 | O servidor não está ligado | Rode `python python/app.py` e deixe o terminal aberto |
| "Resposta inesperada do servidor" no login | Abriu o site pelo Live Server ou clicando no arquivo | Use **http://localhost:5000** |
| `python` não é reconhecido | Python não instalado ou fora do PATH | Instale marcando "Add to PATH", ou use `py` (Windows) / `python3` (Mac/Linux) |
| `No module named flask` / `dotenv` | Faltou instalar as dependências | `python -m pip install -r python/requirements.txt` |
| `Address already in use` / porta ocupada | Outro programa usa a 5000 | Mude a porta (tabela da seção 2) |
| `Cannot GET /tela.html` | Está rodando outro servidor (Node) | Pare o outro e use o do Os-Bode; o endereço é `/html/tela.html` |
| Mapa mostra "sem internet" | O navegador não acessou o OpenStreetMap | Confira a internet; o resto do app funciona |
| Visual antigo depois de atualizar | Cache do navegador | **Ctrl+F5** |
| `git pull` reclama de alterações locais | Há arquivos alterados no seu computador | `git stash -u`, depois `git pull` |
| A loja/conta do colega não aparece | O banco é local de cada máquina | Usem um só computador para a apresentação (seção 2) |

---

## 8. Android Studio (WebView)

O servidor precisa estar ligado em um computador e o celular/emulador acessa por rede. No emulador Android, o endereço do computador é `http://10.0.2.2:5000`. Carregue essa URL no WebView (em vez de `file:///android_asset/...`) e ative `android:usesCleartextTraffic="true"` no `AndroidManifest.xml`, porque o servidor usa http.

## 9. O que ainda falta

- Banco em PostgreSQL, se o professor exigir (hoje é SQLite).
- Configurar um SMTP real para o e-mail de recuperação (o código já está pronto).
- Notificações em tempo real (hoje é consulta a cada 30 s).
- Trocar a senha do banco que ficou no histórico do GitHub (estava no `.env.exemplo` antigo).
- Foto de fundo da estação ferroviária (`js/img/estacao.jpg` não existe).
