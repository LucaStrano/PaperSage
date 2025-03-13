import sqlite3
from typing import Optional, Any, Tuple, List
import threading

# Store connection per thread ID
_DB_CONNECTIONS = {}
_DB_PATH = "app/storage/sqlite/contents.db"

def get_db_connection():
    """Get a thread-local database connection"""
    thread_id = threading.get_ident()
    if thread_id not in _DB_CONNECTIONS:
        _DB_CONNECTIONS[thread_id] = sqlite3.connect(_DB_PATH)
    return _DB_CONNECTIONS[thread_id]

def close_db_connection():
    """Close the database connection for the current thread"""
    thread_id = threading.get_ident()
    if thread_id in _DB_CONNECTIONS:
        _DB_CONNECTIONS[thread_id].close()
        del _DB_CONNECTIONS[thread_id]

def close_all_connections():
    """Close all database connections"""
    for conn in _DB_CONNECTIONS.values():
        conn.close()
    _DB_CONNECTIONS.clear()

def get_paper_info(paper_id: str) -> str:
    """Get paper info based on the paper_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM paper_info WHERE id=?", (paper_id,))
    result = cursor.fetchone()
    if result:
        return result[0]
    print("ERROR: PAPER INFO NOT FOUND!")
    return ""

def get_available_papers() -> List[Tuple[str, str]]:
    """Get list of available papers."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM papers")
    papers = cursor.fetchall()
    return papers

def does_file_exist(file_id: str) -> bool:
    """Check if a file exists in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM papers WHERE id=?", (file_id,))
    result = cursor.fetchone()
    return result is not None

def save_file_to_db(file_id: str, file_name: str) -> None:
    """Save a file to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Explicitly specify column names to avoid the timestamp column issue
    cursor.execute("INSERT INTO papers (id, name) VALUES (?, ?)", (file_id, file_name))
    conn.commit()

def delete_file_from_db(file_id: str) -> None:
    """Delete a file from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM papers WHERE id=?", (file_id,))
    conn.commit()

def insert_paper_info(paper_id: str, content: str) -> None:
    """Insert paper info into the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO paper_info VALUES (?,?)', (paper_id, content))
    conn.commit()
