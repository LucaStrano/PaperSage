CREATE TABLE papers (
    id VARCHAR(16) PRIMARY KEY,
    filename VARCHAR(100) NOT NULL,
    inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE blocks (
    paper_id VARCHAR(16) NOT NULL,
    section_id VARCHAR(16) NOT NULL,
    block VARCHAR(1000) NOT NULL,
    PRIMARY KEY (paper_id, section_id),
    FOREIGN KEY (paper_id) REFERENCES papers(id)
);

CREATE TABLE citations ( 
    paper_id VARCHAR(16) NOT NULL, 
    citation_id VARCHAR(16) NOT NULL, 
    citation_text VARCHAR(200) NOT NULL, 
    PRIMARY KEY (paper_id, citation_id),
    FOREIGN KEY (paper_id) REFERENCES papers(id)
);