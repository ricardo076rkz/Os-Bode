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
