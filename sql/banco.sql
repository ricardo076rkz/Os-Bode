-- ============================================================
-- 1. APAGAR TABELAS EXISTENTES (SE HOUVER)
-- ============================================================
DROP TABLE IF EXISTS evento CASCADE;
DROP TABLE IF EXISTS pedido CASCADE;
DROP TABLE IF EXISTS avaliacao CASCADE;
DROP TABLE IF EXISTS loja CASCADE;
DROP TABLE IF EXISTS logista CASCADE;
DROP TABLE IF EXISTS cliente CASCADE;
DROP TABLE IF EXISTS usuario CASCADE;

-- ============================================================
-- 2. CRIAÇÃO DAS TABELAS
-- ============================================================

-- Tabela Pai
CREATE TABLE usuario (
    id_usuario INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    senha VARCHAR(100) NOT NULL,
    perfil VARCHAR(20) NOT NULL CHECK (perfil IN ('CLIENTE', 'LOGISTA'))
);

-- Tabela Filha: Cliente
CREATE TABLE cliente (
    id_usuario INT PRIMARY KEY REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    endereco VARCHAR(200),
    telefone VARCHAR(20)
);

-- Tabela Filha: Logista (Comerciante/Dono)
CREATE TABLE logista (
    id_usuario INT PRIMARY KEY REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    cnpj VARCHAR(20) UNIQUE NOT NULL
);

-- Tabela: Loja (Ponto no Mapa)
CREATE TABLE loja (
    id_loja INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_logista INT REFERENCES logista(id_usuario) ON DELETE CASCADE,
    nome_loja VARCHAR(100) NOT NULL,
    segmento VARCHAR(50) NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    avaliacao_media DECIMAL(2, 1) DEFAULT 5.0
);

-- Tabela: Avaliacao
CREATE TABLE avaliacao (
    id_avaliacao INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_cliente INT REFERENCES cliente(id_usuario) ON DELETE CASCADE,
    id_loja INT REFERENCES loja(id_loja) ON DELETE CASCADE,
    nota INT CHECK (nota BETWEEN 1 AND 5),
    comentario TEXT,
    data_criacao DATE DEFAULT CURRENT_DATE
);

-- Tabela: Pedido (Reserva para Retirada Presencial)
CREATE TABLE pedido (
    id_pedido INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_cliente INT REFERENCES cliente(id_usuario) ON DELETE CASCADE,
    id_loja INT REFERENCES loja(id_loja) ON DELETE CASCADE,
    item VARCHAR(150) NOT NULL,
    valor DECIMAL(10, 2) NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela: Evento (Grande Motofest)
CREATE TABLE evento (
    id_evento INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    dia_semana VARCHAR(20) NOT NULL,
    horario VARCHAR(20) NOT NULL,
    descricao TEXT,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL
);

-- ============================================================
-- 3. MASSA DE DADOS DE TESTE (CARUARU CENTRO)
-- ============================================================

-- Inserindo Usuários
INSERT INTO usuario (nome, email, senha, perfil) VALUES
('Maria Silva', 'maria@email.com', '123456', 'CLIENTE'),
('Carlos Dono', 'carlos@email.com', '123456', 'LOGISTA'),
('Ana Comerciante', 'ana@email.com', '123456', 'LOGISTA');

-- Inserindo Detalhes do Cliente
INSERT INTO cliente (id_usuario, endereco, telefone) VALUES
(1, 'Rua Quinze de Novembro, Centro - Caruaru', '(81) 99999-1111');

-- Inserindo Detalhes dos Logistas
INSERT INTO logista (id_usuario, cnpj) VALUES
(2, '11.222.333/0001-44'),
(3, '55.666.777/0001-88');

-- Inserindo Lojas (Trecho Estação Ferroviária -> Catedral)
INSERT INTO loja (id_logista, nome_loja, segmento, latitude, longitude, avaliacao_media) VALUES
(2, 'Café da Estação', 'Cafeteria', -8.283000, -35.976000, 4.9),
(3, 'Artesanato Caruaru', 'Souvenirs', -8.282800, -35.973000, 4.7);

-- Inserindo Avaliação
INSERT INTO avaliacao (id_cliente, id_loja, nota, comentario) VALUES
(1, 1, 5, 'Ótimo atendimento e excelente localização perto do Polo da Estação!');

-- Inserindo Pedido de Retirada
INSERT INTO pedido (id_cliente, id_loja, item, valor) VALUES
(1, 1, 'Café Expresso + Bolo de Rolo', 18.50);

-- Inserindo Evento Motofest
INSERT INTO evento (nome, dia_semana, horario, descricao, latitude, longitude) VALUES
('Grande Motofest', 'Quinta-feira', '19:00', 'Encontro de motociclistas no Polo da Estação Ferroviária', -8.283500, -35.976500);

-- Listar todas as lojas

SELECT nome_loja, segmento, latitude, longitude, avaliacao_media 
FROM loja;

-- Consultar reservas pedidos e tals

SELECT u.nome AS cliente, l.nome_loja, p.item, p.valor, p.criado_em
FROM pedido p
JOIN cliente c ON p.id_cliente = c.id_usuario
JOIN usuario u ON c.id_usuario = u.id_usuario
JOIN loja l ON p.id_loja = l.id_loja;

-- Buscar Evento

SELECT nome, horario, descricao, latitude, longitude 
FROM evento 
WHERE dia_semana = 'Quinta-feira';


