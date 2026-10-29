CREATE TABLE IF NOT EXISTS articles (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    authors VARCHAR(255),
    publication_year INT,
    doi VARCHAR(100) UNIQUE,
    abstract TEXT,
    priority VARCHAR(2) DEFAULT 'P2' CHECK (priority IN ('P1', 'P2', 'P3')),
    status VARCHAR(20) DEFAULT 'Unread' CHECK (status IN ('Unread', 'In Progress', 'Read', 'Archived')),
    tags VARCHAR(255), -- E.g., "AI, Healthcare, Algorithms"
    pdf_path VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);