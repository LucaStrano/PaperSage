import sqlite3
import hashlib

### --- DB UTILITY FUNCTIONS --- ###

def calculate_hash(content : bytes, buffer_size : int = 4096) -> str:
    """Returns the truncated hash of the content using a buffer with `buffer_size` chunks."""
    hash_obj = hashlib.md5()
    for i in range(0, len(content), buffer_size):
        chunk = content[i:i+buffer_size]
        hash_obj.update(chunk)
    full_hash = hash_obj.hexdigest()
    truncated_hash = full_hash[:len(full_hash)//2]
    return truncated_hash

def does_file_exist(cursor: sqlite3.Cursor, file_id: str) -> bool:
    """Check if a file with the given ID exists in the database"""
    cursor.execute("SELECT name FROM papers WHERE id = ?", (file_id,))
    result = cursor.fetchone()
    return result is not None
    
def save_file_to_db(cursor : sqlite3.Cursor, connection : sqlite3.Connection, file_id: str, file_name: str) -> None:
    """Save the file to the database. Raises an exception if unsuccessful."""
    cursor.execute("INSERT INTO papers (id, name) VALUES (?, ?)", (file_id, file_name))
    cursor.connection.commit()