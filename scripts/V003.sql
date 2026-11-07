CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Para la entidad Usuario
ALTER TABLE users
ADD COLUMN is_active BOOLEAN DEFAULT TRUE NOT NULL,
ADD COLUMN deleted_at TIMESTAMP NULL;

-- Para la entidad Artículo (u otras entidades del sistema)
ALTER TABLE articles
ADD COLUMN is_active BOOLEAN DEFAULT TRUE NOT NULL,
ADD COLUMN deleted_at TIMESTAMP NULL;