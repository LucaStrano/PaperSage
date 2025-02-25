import os
import sqlite3

# Create the directory if it doesn't exist
dbdir_path = os.path.join("app", "storage", "sqlite")
os.makedirs(dbdir_path, exist_ok=True)

# Create the SQLite database file
conn = sqlite3.connect(os.path.join(dbdir_path, "contents.db"))
c = conn.cursor()

# papers table
c.execute("""\
CREATE TABLE IF NOT EXISTS papers (
    id VARCHAR(32) PRIMARY KEY, 
    name TEXT NOT NULL,
    add_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)""")

conn.commit()
c.close()
conn.close()