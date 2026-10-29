-- 1. Tabla de Autores
CREATE TABLE IF NOT EXISTS authors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE
);

-- 2. Tabla de Artículos
CREATE TABLE IF NOT EXISTS articles (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    publication_year INT,
    doi VARCHAR(100) UNIQUE,
    abstract TEXT,
    priority VARCHAR(2) DEFAULT 'P2' CHECK (priority IN ('P1', 'P2', 'P3')),
    status VARCHAR(20) DEFAULT 'Unread' CHECK (status IN ('Unread', 'In Progress', 'Read', 'Archived')),
    tags VARCHAR(255),
    pdf_path VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Tabla Intermedia
CREATE TABLE IF NOT EXISTS article_authors (
    article_id INT REFERENCES articles(id) ON DELETE CASCADE,
    author_id INT REFERENCES authors(id) ON DELETE CASCADE,
    PRIMARY KEY (article_id, author_id)
);