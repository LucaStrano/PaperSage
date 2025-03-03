import sqlite3
import os
import sys
from qdrant_client import models, QdrantClient

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
from app.config_loader import ConfigLoader

def delete_from_collection_with_id(collection_name : str, paper_id : str):
    """
    Deletes all data points from the Qdrant collection with the given ID.
    """
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

# Check if an ID was provided as an argument
paper_id = None
if len(sys.argv) > 1:
    paper_id = sys.argv[1]

config = ConfigLoader().get_config()

db_path = os.path.join("app", "storage", "sqlite", "contents.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()


try:

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
        
        delete_from_collection_with_id(
            collection_name=config['qdrant_config']['text_collection_name'], 
            paper_id=paper_id
        )
        delete_from_collection_with_id(
            collection_name=config['qdrant_config']['image_collection_name'],
            paper_id=paper_id
        )

    else: # Delete all entries

        cursor.execute("DELETE FROM papers")
        cursor.execute("DELETE FROM paper_info")
        conn.commit()
        print("All papers deleted from SQLite database.")
        
        # Recreate colletion
        if client.delete_collection(collection_name=config['qdrant_config']['text_collection_name'])\
        and client.delete_collection(collection_name=config['qdrant_config']['image_collection_name']):
            print("Collections deleted.")
        else:
            print("Error Deleting Collections.")
            
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    conn.close()