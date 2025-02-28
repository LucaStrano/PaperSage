import os
import sqlite3
from qdrant_client import QdrantClient, models
import yaml

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

conn.commit()
c.close()
conn.close()
print("✅ SQLite3 database created.")

# QDRANT CONFIG
print("Creating Qdrant collection...")
settings = yaml.safe_load(open("config.yaml", "r"))
print(settings)
qdrantdir_path = os.path.join("app", "storage", "qdrant")
os.makedirs(qdrantdir_path, exist_ok=True)

client = QdrantClient(path=os.path.join(qdrantdir_path, "vectorstore"))
client.create_collection(
    collection_name=settings['configs'][1]['qdrant_config'][0]['collection_name'], 
    vectors_config=models.VectorParams(
        size=settings['configs'][2]['embedding_config'][2]['output_length'], 
        distance=models.Distance.COSINE
    ),
)
client.close()
print("✅ Qdrant collection created.")