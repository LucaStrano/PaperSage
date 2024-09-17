CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE papers (
    id VARCHAR(16) PRIMARY KEY,
    filename VARCHAR(100) NOT NULL,
    inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE blocks (
    paper_id VARCHAR(16) NOT NULL,
    section_id VARCHAR(16) NOT NULL,
    content VARCHAR(1000) NOT NULL,
    PRIMARY KEY (paper_id, section_id),
    FOREIGN KEY (paper_id) REFERENCES papers(id)
);

/*REATE TABLE chunks (
    id BIGSERIAL PRIMARY KEY,
    paper_id VARCHAR(16) NOT NULL,
    content TEXT NOT NULL,
    embedding vector(768),
);

CREATE TABLE images (
    id BIGSERIAL NOT NULL,
    content TEXT NOT NULL,
    embedding vector(768),
    PRIMARY KEY (paper_id, chunk_id)
);*/