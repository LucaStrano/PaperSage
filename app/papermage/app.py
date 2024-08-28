# This runs on port 8000

from fastapi import FastAPI, UploadFile
from fastapi.responses import JSONResponse
import os
import psycopg2 as pg
from utils import *
import signal

# from dotenv import load_dotenv
# load_dotenv()

## ---- CONFIGS ---- ##

# Ensure environment variables are set
db_name = os.environ.get("POSTGRES_DB")
db_user = os.environ.get("POSTGRES_USER")
db_password = os.environ.get("POSTGRES_PASSWORD")

if not db_name or not db_user or not db_password:
    raise ValueError("Database environment variables are not set")

conn = pg.connect(
    database=db_name,
    user=db_user,
    password=db_password,
    host="http://localhost:5432",
    port="5432"
)
cursor = conn.cursor()

# Clean database connection on shutdown
def handle_signal(signum, frame):
    print(f"Received signal {signum}. Shutting down...")
    try:
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error closing database connection: {e}")
    finally:
        exit(0)

signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

## ---- UTILITY DB FUNCTIONS ---- ##

def does_file_exist(file_id : str) -> bool:
    """Check if a file with the given ID exists in the database"""
    try:
        cursor.execute("SELECT filename FROM papers WHERE id = %s", (file_id,))
        result = cursor.fetchone()
        return result is not None
    except pg.DatabaseError as e:
        print(f"Error checking for existing file: {e}")
        return True # Avoid errors by not processing files that might already exist
    
def save_file(file_id : str, file_name : str) -> bool:
    """Save the file to the database. Returns True if successful, False otherwise"""
    try:
        cursor.execute("INSERT INTO papers (id, filename) VALUES (%s, %s)", (file_id, file_name))
        conn.commit()
        return True
    except pg.DatabaseError as e:
        print(f"Error saving file: {e}")
        return False

## ---- FASTAPI ROUTES ---- ##

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/process")
async def process(file: UploadFile):
    
    # Read the contents of the uploaded file
    file_contents = await file.read()
    print(f"RECEIVED {file.filename}")

    file_id = calculate_hash(file_contents)

    if does_file_exist(file_id):
        print(f"File {file_id} already processed.")
        return JSONResponse(content={"status": "File already processed."}, status_code=409)
    
    if not save_file(file_id, file.filename):
        print(f"Error saving file {file_id}")
        return JSONResponse(content={"status": "Error saving file."}, status_code=500)
    
    return {"status": "ok"}