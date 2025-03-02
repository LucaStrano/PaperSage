import sqlite3
import os
import sys
from qdrant_client import models, QdrantClient

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
from app.config_loader import ConfigLoader

# Check if an ID was provided as an argument
paper_id = None
if len(sys.argv) > 1:
    paper_id = sys.argv[1]

config = ConfigLoader().get_config()

db_path = os.path.join("app", "storage", "sqlite", "contents.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()


try:
    collection_name = config['qdrant_config']['collection_name']
    qdrantclient_path = os.path.join("app", "storage", "qdrant", "vectorstore")
    client = QdrantClient(path=qdrantclient_path)
    
    if paper_id:

        print(f"Deleting paper with ID: {paper_id}")
        
        # Delete from SQLite
        cursor.execute("DELETE FROM papers WHERE id = ?", (paper_id,))
        cursor.execute("DELETE FROM paper_info WHERE id = ?", (paper_id,))
        deleted_rows = cursor.rowcount
        conn.commit()
        
        if deleted_rows == 0:
            print(f"No paper found with ID: {paper_id}")
        else:
            print(f"Deleted {deleted_rows} row(s) from SQLite database.")
        
        # Delete from Qdrant
        res = client.delete(
            collection_name=collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(key="id",match=models.MatchValue(value=paper_id)),
                    ],
                )
            ),
        )
        print(res) # TODO add more insights
    else:
        # Delete all entries
        cursor.execute("DELETE FROM papers")
        cursor.execute("DELETE FROM paper_info")
        conn.commit()
        print("All papers deleted from SQLite database.")
        
        # Recreate colletion
        client.delete_collection(collection_name=collection_name)
        client.create_collection(
            collection_name=config['qdrant_config']['collection_name'], 
            vectors_config=models.VectorParams(
                size=config['embedding_config']['output_length'], 
                distance=models.Distance.COSINE
            ),
        )
        print("All data points deleted from Vector Store.")
            
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    conn.close()