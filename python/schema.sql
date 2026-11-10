-- Nordestinando - tabelas do banco (SQLite)
-- Mesma modelagem do sql/banco.sql, ampliada para o cadastro completo do comerciante.

CREATE TABLE IF NOT EXISTS usuario (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nome       TEXT NOT NULL,
    email      TEXT NOT NULL UNIQUE,
    telefone   TEXT,
    senha_hash TEXT NOT NULL,
    perfil     TEXT NOT NULL CHECK (perfil IN ('CLIENTE', 'LOGISTA')),
    criado_em  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS logista (
    id_usuario   INTEGER PRIMARY KEY REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    cnpj         TEXT UNIQUE,
    razao_social TEXT
);

CREATE TABLE IF NOT EXISTS loja (
    id_loja       INTEGER PRIMARY KEY AUTOINCREMENT,
    id_logista    INTEGER NOT NULL UNIQUE REFERENCES logista(id_usuario) ON DELETE CASCADE,
    nome_fantasia TEXT NOT NULL,
    segmento      TEXT NOT NULL,
    descricao     TEXT NOT NULL,
    cep           TEXT NOT NULL,
    rua           TEXT NOT NULL,
    numero        TEXT NOT NULL,
    bairro        TEXT NOT NULL,
    cidade        TEXT NOT NULL,
    estado        TEXT NOT NULL,
    latitude      REAL NOT NULL,
    longitude     REAL NOT NULL,
    horarios      TEXT NOT NULL,
    telefone      TEXT NOT NULL,
    whatsapp      TEXT,
    instagram     TEXT,
    site          TEXT,
    logo          TEXT,
    foto          TEXT
);

CREATE TABLE IF NOT EXISTS item_vitrine (
    id_item INTEGER PRIMARY KEY AUTOINCREMENT,
    id_loja INTEGER NOT NULL REFERENCES loja(id_loja) ON DELETE CASCADE,
    nome    TEXT NOT NULL,
    valor   REAL NOT NULL CHECK (valor >= 0),
    foto    TEXT
);

CREATE TABLE IF NOT EXISTS avaliacao (
    id_avaliacao INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente   INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    id_loja      INTEGER NOT NULL REFERENCES loja(id_loja) ON DELETE CASCADE,
    nota         INTEGER NOT NULL CHECK (nota BETWEEN 1 AND 5),
    comentario   TEXT,
    data_criacao TEXT NOT NULL DEFAULT CURRENT_DATE,
    UNIQUE (id_cliente, id_loja)
);

CREATE TABLE IF NOT EXISTS pedido (
    id_pedido  INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    id_loja    INTEGER NOT NULL REFERENCES loja(id_loja) ON DELETE CASCADE,
    item       TEXT NOT NULL,
    valor      REAL NOT NULL,
    criado_em  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evento (
    id_evento  INTEGER PRIMARY KEY AUTOINCREMENT,
    id_loja    INTEGER NOT NULL REFERENCES loja(id_loja) ON DELETE CASCADE,
    nome       TEXT NOT NULL,
    dia_semana TEXT NOT NULL,
    horario    TEXT NOT NULL,
    descricao  TEXT,
    latitude   REAL,
    longitude  REAL
);

-- ---------------------------------------------------------------- conta, segurança e notificações
-- sessões ativas (o cookie guarda um token; aqui fica só o hash dele)
CREATE TABLE IF NOT EXISTS sessao (
    id_sessao  INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    criado_em  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ultimo_uso TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip         TEXT,
    agente     TEXT
);

CREATE TABLE IF NOT EXISTS notificacao (
    id_notificacao INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario     INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    categoria      TEXT NOT NULL CHECK (categoria IN ('avaliacoes', 'pedidos', 'eventos', 'seguranca')),
    titulo         TEXT NOT NULL,
    mensagem       TEXT NOT NULL,
    link           TEXT,
    lida           INTEGER NOT NULL DEFAULT 0,
    criada_em      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_notificacao_usuario ON notificacao (id_usuario, lida, id_notificacao);

-- histórico de atividades da conta
CREATE TABLE IF NOT EXISTS atividade (
    id_atividade INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario   INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    acao         TEXT NOT NULL,
    detalhe      TEXT,
    criada_em    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_atividade_usuario ON atividade (id_usuario, id_atividade);

-- limite de tentativas (login e "esqueci a senha")
CREATE TABLE IF NOT EXISTS tentativa (
    id_tentativa INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo         TEXT NOT NULL,
    chave        TEXT NOT NULL,
    criada_em    REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tentativa ON tentativa (tipo, chave, criada_em);

-- links de redefinição de senha (só o hash do token é guardado)
CREATE TABLE IF NOT EXISTS redefinicao_senha (
    token_hash TEXT PRIMARY KEY,
    id_usuario INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    expira_em  REAL NOT NULL,
    usada      INTEGER NOT NULL DEFAULT 0
);

-- ---------------------------------------------------------------- agenda da cidade
-- Eventos e feiras de Caruaru. Para incluir um novo, basta uma linha aqui
-- (ou no arquivo python/dados/eventos_cidade.json): a tela monta o card sozinha.
CREATE TABLE IF NOT EXISTS evento_cidade (
    id_evento_cidade INTEGER PRIMARY KEY AUTOINCREMENT,
    slug        TEXT NOT NULL UNIQUE,
    titulo      TEXT NOT NULL,
    categoria   TEXT NOT NULL,
    dia_semana  TEXT NOT NULL,           -- Segunda ... Domingo
    periodo     TEXT NOT NULL CHECK (periodo IN ('manha', 'tarde', 'noite')),
    horario     TEXT,                    -- só quando confirmado; vazio = "a confirmar"
    local_nome  TEXT NOT NULL,
    busca_mapa  TEXT,                    -- texto usado para achar o local no mapa
    latitude    REAL,
    longitude   REAL,
    descricao   TEXT NOT NULL,
    detalhes    TEXT NOT NULL DEFAULT '[]',   -- lista (JSON) de informações confirmadas
    pendencias  TEXT NOT NULL DEFAULT '[]',   -- lista (JSON) do que ainda precisa ser validado
    foto        TEXT,                    -- endereço ou data URL da foto (quando houver autorização/procedência)
    ativo       INTEGER NOT NULL DEFAULT 1
);

-- ---------------------------------------------------------------- gamificação, vouchers e Nordestinando+
-- carteira de pontos (o saldo SEMPRE vive aqui, no servidor; nunca no navegador)
CREATE TABLE IF NOT EXISTS carteira (
    id_usuario  INTEGER PRIMARY KEY REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    saldo       INTEGER NOT NULL DEFAULT 0 CHECK (saldo >= 0),
    total_ganho INTEGER NOT NULL DEFAULT 0,
    total_usado INTEGER NOT NULL DEFAULT 0
);

-- razão: toda movimentação de pontos fica registrada. "chave" é única e impede recompensa em duplicidade.
CREATE TABLE IF NOT EXISTS movimento_pontos (
    id_movimento  INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario    INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    tipo          TEXT NOT NULL CHECK (tipo IN ('avaliacao', 'resgate', 'estorno')),
    pontos        INTEGER NOT NULL,            -- com sinal: ganho (+) ou uso (-)
    pontos_base   INTEGER NOT NULL DEFAULT 0,  -- antes do multiplicador
    pontos_bonus  INTEGER NOT NULL DEFAULT 0,  -- parte vinda do Premium
    multiplicador INTEGER NOT NULL DEFAULT 1,
    descricao     TEXT NOT NULL,
    id_loja       INTEGER REFERENCES loja(id_loja) ON DELETE SET NULL,
    id_avaliacao  INTEGER REFERENCES avaliacao(id_avaliacao) ON DELETE SET NULL,
    id_voucher    INTEGER,
    chave         TEXT NOT NULL UNIQUE,
    saldo_apos    INTEGER NOT NULL,
    criado_em     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_movimento_usuario ON movimento_pontos (id_usuario, id_movimento);

CREATE TABLE IF NOT EXISTS promocao (
    id_promocao          INTEGER PRIMARY KEY AUTOINCREMENT,
    id_loja              INTEGER NOT NULL REFERENCES loja(id_loja) ON DELETE CASCADE,
    titulo               TEXT NOT NULL,
    descricao            TEXT NOT NULL,
    tipo_beneficio       TEXT NOT NULL CHECK (tipo_beneficio IN ('percentual', 'valor_fixo', 'brinde', 'especial', 'outro')),
    valor_beneficio      REAL,
    pontos_necessarios   INTEGER NOT NULL CHECK (pontos_necessarios > 0),
    quantidade_total     INTEGER NOT NULL CHECK (quantidade_total > 0),
    quantidade_resgatada INTEGER NOT NULL DEFAULT 0,
    limite_por_usuario   INTEGER NOT NULL DEFAULT 1 CHECK (limite_por_usuario > 0),
    inicio               TEXT NOT NULL,
    fim                  TEXT NOT NULL,
    condicoes            TEXT NOT NULL DEFAULT '',
    status               TEXT NOT NULL DEFAULT 'ativa' CHECK (status IN ('ativa', 'pausada', 'encerrada')),
    criada_em            TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (quantidade_resgatada <= quantidade_total)
);

CREATE TABLE IF NOT EXISTS voucher (
    id_voucher    INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo        TEXT NOT NULL UNIQUE,
    id_promocao   INTEGER NOT NULL REFERENCES promocao(id_promocao) ON DELETE CASCADE,
    id_usuario    INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    pontos_gastos INTEGER NOT NULL,
    status        TEXT NOT NULL DEFAULT 'resgatado' CHECK (status IN ('resgatado', 'utilizado', 'cancelado')),
    validade      TEXT NOT NULL,
    resgatado_em  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    utilizado_em  TEXT,
    validado_por  INTEGER REFERENCES usuario(id_usuario) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_voucher_usuario ON voucher (id_usuario);
CREATE INDEX IF NOT EXISTS idx_voucher_promocao ON voucher (id_promocao);

-- assinatura Nordestinando+ (o estado "expirada" é calculado pela data de fim)
CREATE TABLE IF NOT EXISTS assinatura (
    id_assinatura   INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario      INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    status          TEXT NOT NULL CHECK (status IN ('ativa', 'cancelada')),
    inicio          TEXT NOT NULL,
    fim             TEXT NOT NULL,
    valor_centavos  INTEGER NOT NULL,
    ambiente        TEXT NOT NULL CHECK (ambiente IN ('demo', 'producao')),
    criada_em       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cancelada_em    TEXT
);
CREATE INDEX IF NOT EXISTS idx_assinatura_usuario ON assinatura (id_usuario, id_assinatura);

-- pagamentos: só 'confirmado' (vindo do gateway) conta como receita. 'demo' é simulação identificada.
CREATE TABLE IF NOT EXISTS pagamento (
    id_pagamento       INTEGER PRIMARY KEY AUTOINCREMENT,
    id_assinatura      INTEGER NOT NULL REFERENCES assinatura(id_assinatura) ON DELETE CASCADE,
    valor_centavos     INTEGER NOT NULL,
    status             TEXT NOT NULL CHECK (status IN ('pendente', 'confirmado', 'falhou', 'demo')),
    gateway            TEXT NOT NULL,
    referencia_externa TEXT UNIQUE,
    criado_em          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------- LGPD
-- registro de aceite dos documentos (prova de consentimento: qual versão, quando)
CREATE TABLE IF NOT EXISTS consentimento (
    id_consentimento INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario       INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    documento        TEXT NOT NULL CHECK (documento IN ('termos', 'privacidade')),
    versao           TEXT NOT NULL,
    aceito_em        TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_consentimento ON consentimento (id_usuario);

-- pedidos dos titulares (acesso, correção, exclusão, etc.) para acompanhar o prazo legal
CREATE TABLE IF NOT EXISTS solicitacao_titular (
    id_solicitacao INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario     INTEGER REFERENCES usuario(id_usuario) ON DELETE SET NULL,
    tipo           TEXT NOT NULL,
    criada_em      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
