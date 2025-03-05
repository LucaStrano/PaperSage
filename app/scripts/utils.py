import sqlite3
import hashlib
from PIL import Image
from typing import Any, List
import torch.nn.functional as F

### --- DB UTILITY FUNCTIONS --- ###

async def calculate_hash(content : bytes, buffer_size : int = 4096) -> str:
    """[ASYNC] Returns the truncated hash of the content using a buffer with `buffer_size` chunks."""
    hash_obj = hashlib.md5()
    for i in range(0, len(content), buffer_size):
        chunk = content[i:i+buffer_size]
        hash_obj.update(chunk)
    full_hash = hash_obj.hexdigest()
    truncated_hash = full_hash[:len(full_hash)//2]
    return truncated_hash

async def does_file_exist(cursor: sqlite3.Cursor, file_id: str) -> bool:
    """[ASYNC] Check if a file with the given ID exists in the database"""
    cursor.execute("SELECT name FROM papers WHERE id = ?", (file_id,))
    result = cursor.fetchone()
    return result is not None
    
async def save_file_to_db(cursor : sqlite3.Cursor, connection : sqlite3.Connection, file_id: str, file_name: str) -> None:
    """[ASYNC] Save the file to the database. Raises an exception if unsuccessful."""
    cursor.execute("INSERT INTO papers (id, name) VALUES (?, ?)", (file_id, file_name))
    cursor.connection.commit()

### -- VECTOR STORE SUPPORT FUNCTIONS -- ###


def embed_image(image : Image, img_model : Any, processor : Any, shortest_edge = 224) -> List[float]:
    """
    Embeds the image using the image model.
    Args:
        image (Image): Image object.
        img_model (Any): Image model loaded with AutoModel.
        processor (Any): Processor loaded with AutoImageProcessor.
        shortest_edge (int): Shortest edge parameter to pass to processor.
    Returns:
        List[float]: List of floats representing the image embedding.
    """
    # Process the image with the processor
    inputs = processor(image, return_tensors="pt", size={"shortest_edge": shortest_edge})
    img_emb = img_model(**inputs).last_hidden_state
    img_embeddings = F.normalize(img_emb[:, 0], p=2, dim=1)
    return img_embeddings[0].tolist()