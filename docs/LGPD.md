# LGPD no Nordestinando (Lei 13.709/2018)

> Documento técnico da equipe. **Não substitui parecer jurídico.** Antes de operar comercialmente, um advogado ou encarregado (DPO) deve revisar os textos das páginas `privacidade.html` e `termos.html`.

## Mapa dos dados (art. 37)
| Dado | Onde | Finalidade | Base legal | Retenção |
|---|---|---|---|---|
| Nome, e-mail, telefone | `usuario` | conta e contato | execução de contrato (art. 7º, V) | enquanto a conta existir |
| Senha | `usuario.senha_hash` (hash) | autenticação | execução de contrato | idem |
| Foto de perfil | `usuario.avatar` | personalização (opcional) | consentimento (art. 7º, I) | até remover ou excluir a conta |
| Avaliações, fotos, pedidos | `avaliacao`, `pedido` | funcionamento do guia | execução de contrato | idem |
| Pontos, vouchers, assinatura | `carteira`, `movimento_pontos`, `voucher`, `assinatura`, `pagamento` | recompensas e Nordestinando+ | execução de contrato | idem (dados fiscais reais, se existirem, pelo prazo legal) |
| CNPJ, razão social, loja | `logista`, `loja` | cadastro do comerciante | execução de contrato | idem |
| IP e navegador das sessões | `sessao` | segurança | legítimo interesse (art. 7º, IX) | 60 dias sem uso |
| Histórico de atividades | `atividade` | segurança e transparência | legítimo interesse | 365 dias |
| Tentativas de login | `tentativa` | antifraude | legítimo interesse | 24 h |
| Aceite dos documentos | `consentimento` | prova de consentimento | obrigação/exercício de direitos (art. 16, I) | enquanto a conta existir |
| Pedidos de titulares | `solicitacao_titular` | prazo legal | cumprimento de obrigação | exclusão não identifica a pessoa |

Não são coletados dados sensíveis. Não há publicidade, perfilamento nem venda de dados.

## Direitos do titular (art. 18) e onde estão
- Acesso e portabilidade: Configurações > "Baixar uma cópia dos meus dados" (`GET /api/lgpd/meus-dados`, JSON).
- Correção: Perfil (`PATCH /api/conta`).
- Exclusão: Configurações > Excluir conta (`DELETE /api/conta`); a cascata do banco apaga tudo do titular (testado em `tests/teste_lgpd_api.py`).
- Revogação de consentimento: remover a foto; não há outro consentimento opcional hoje.
- Informação sobre compartilhamento: Política de Privacidade.
- Prazo de resposta prometido: 15 dias.

## Transferência a terceiros (navegador do usuário)
unpkg.com (Leaflet), tile.openstreetmap.org, nominatim.openstreetmap.org, viacep.com.br, api.open-meteo.com. Recebem o IP do usuário; não recebem nome ou e-mail. Declarado na política. Para zerar isso, hospedar o Leaflet localmente e usar um servidor de tiles próprio.

## Medidas de segurança (art. 46)
Hash de senha (werkzeug), sessões com token em hash e revogáveis, limite de tentativas, cabeçalhos (nosniff, X-Frame-Options, Referrer-Policy, Permissions-Policy, HSTS com `COOKIE_SEGURO=1`), permissões por perfil no servidor, validação de entradas, limpeza automática por prazo.

## Plano de resposta a incidentes (art. 48)
1. Conter: trocar `SECRET_KEY`, encerrar sessões (`DELETE FROM sessao`), corrigir a falha.
2. Avaliar: quais dados e quantas pessoas; há risco relevante?
3. Comunicar ANPD e titulares afetados em prazo razoável (a ANPD indica 3 dias úteis), com natureza dos dados, medidas e riscos.
4. Registrar o incidente e as ações.

## O que depende do operador (não dá para fazer só no código)
- Nomear o encarregado e definir `LGPD_CONTATO_EMAIL` e `LGPD_CONTROLADOR` no `.env` (a página mostra "ainda não informado" até isso).
- Revisão jurídica dos textos e eventual RIPD (relatório de impacto).
- Em produção: HTTPS (`COOKIE_SEGURO=1`), backups criptografados, banco de produção com controle de acesso.
- Rotacionar a senha antiga do banco que ficou no histórico do Git.
