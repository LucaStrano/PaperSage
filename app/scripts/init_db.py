import os
import sqlite3
from qdrant_client import QdrantClient, models
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
from app.config_loader import ConfigLoader


configs = ConfigLoader().get_config()

print("Creating Images Directory...")
imgdir_path = os.path.join("app", "storage", "images")
os.makedirs(imgdir_path, exist_ok=True)
print("✅ Images Directory created.")

# SQLITE3 CONFIG
print("Creating SQLite3 database...")
dbdir_path = os.path.join("app", "storage", "sqlite")
os.makedirs(dbdir_path, exist_ok=True)

conn = sqlite3.connect(os.path.join(dbdir_path, "contents.db"))
c = conn.cursor()

c.execute("""\
CREATE TABLE IF NOT EXISTS papers (
    id VARCHAR(32) PRIMARY KEY, 
    name TEXT NOT NULL,
    add_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)""")

c.execute("""\
CREATE TABLE IF NOT EXISTS paper_info (
    id VARCHAR(32) PRIMARY KEY, 
    content TEXT NOT NULL,
    FOREIGN KEY (id) REFERENCES papers(id)
)""")

conn.commit()
c.close()
conn.close()
print("✅ SQLite3 database created.")

# QDRANT CONFIG
print("Creating Qdrant collections...")
qdrantdir_path = os.path.join("app", "storage", "qdrant")
os.makedirs(qdrantdir_path, exist_ok=True)

client = QdrantClient(path=os.path.join(qdrantdir_path, "vectorstore"))
emb_dize = configs['embedding_config']['output_length']
same_length = configs['embedding_config']['use_same_output_length']

try:
    # text collection
    client.create_collection(
        collection_name=configs['qdrant_config']['text_collection_name'], 
        vectors_config=models.VectorParams(
                size=emb_dize, 
                distance=models.Distance.COSINE
        )
    )
except ValueError as e:
    if 'already exists' in str(e):
        print("Text Collection already exists.")
    else:
        print("Error creating Text collection:", e)

try:
    #image collection
    client.create_collection(
        collection_name=configs['qdrant_config']['image_collection_name'], 
        vectors_config=models.VectorParams(
                size=emb_dize if same_length else configs['embedding_config']['img_output_length'], 
                distance=models.Distance.COSINE
        )
    )
    print("✅ Qdrant collections created.")
except ValueError as e:
    if 'already exists' in str(e):
        print("Image Collection already exists.")
    else:
        print("Error creating Image collection:", e)
finally:
    client.close()