# Próximos passos do Nordestinando

Lista do que falta, em ordem de prioridade. Para retomar com o Claude: abra uma conversa nova, aponte este repositório (`ricardo076rkz/Os-Bode`, branch `front-unificado`) e diga "continuar o docs/PROXIMOS_PASSOS.md".

## 1. Antes da apresentação (fazer primeiro)

- [ ] Rodar o app em **mais de um computador** e confirmar com internet: mapa, busca de endereço, CEP e clima (aqui só foram testados com respostas simuladas).
- [ ] Juntar a branch `front-unificado` na `main` (Pull Request).
- [ ] Trocar a senha do banco que ficou no histórico do GitHub (estava no `.env.exemplo` antigo).
- [ ] Decidir onde o app roda na apresentação: um computador só (banco local) ou hospedado (todos veem os mesmos dados).
- [ ] Testar no Android Studio (emulador acessa `http://10.0.2.2:5000`).

## 2. Funcionalidades que faltam

- [ ] **Favoritos** e **ofertas/promoções** (estavam no escopo original do projeto do grupo e ainda não existem).
- [ ] Recuperação de senha por e-mail (hoje a tela só avisa que não existe).
- [ ] Editar perfil, trocar senha e excluir conta.
- [ ] Banco em PostgreSQL, se o professor exigir (hoje é SQLite; `python/schema.sql` é a base).
- [ ] Foto de fundo da estação ferroviária (`js/img/estacao.jpg` não existe).
- [ ] Fotos de produtos de exemplo em `js/img/`.

## 3. Modo teste (pedido do grupo)

Versão para demonstração, **sem cadastro**: qualquer e-mail e senha entram e dá para mexer normalmente.

- Criar numa branch separada chamada `teste` (um repositório novo no GitHub precisa ser criado pelo dono da conta; a branch dentro do Os-Bode não precisa).
- Servidor com a variável `MODO_TESTE=1`: o login aceita qualquer e-mail e senha, cria a conta na hora e, se for comerciante, cria uma loja de exemplo com vitrine e eventos.
- Aviso visível na tela ("modo de teste") e **nunca** ligado por padrão, para não ir para produção por engano.

## 4. Segurança e qualidade

- [ ] Limite de tentativas de login (hoje não há).
- [ ] Duração máxima da sessão e cookie `Secure` quando houver HTTPS.
- [ ] Mover os testes automáticos (hoje fora do repositório) para uma pasta `tests/`.
- [ ] Imagens hoje ficam dentro do banco; para muitas lojas, guardar em arquivos.
- [ ] Revisar acessibilidade (foco no teclado, leitores de tela) e testar em celulares reais.

## 5. Avaliação da paleta

Barro `#911a1a`, sol `#f2a81d`, mata `#1f7a5c`, papel `#f8f1e2`, tinta `#2a1710`. Todos os textos passam no contraste mínimo (4,5:1); o único fraco era o texto de exemplo dos campos, já corrigido. Verde só para "aberto", amarelo para nota e dia do evento, vermelho para ações e erros: manter assim.
