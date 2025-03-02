import sqlite3
import os

# Get the absolute path to the database file
db_path = os.path.join("app", "storage", "sqlite", "contents.db")

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Delete all entries from the papers table
    cursor.execute("DELETE FROM papers")
    conn.commit()
except sqlite3.Error as e:
    print(f"An error occurred: {e}")
finally:
    # Close the connection
    conn.close()