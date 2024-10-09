# This runs on port 8000

from fastapi import FastAPI, UploadFile
from fastapi.responses import JSONResponse
import os
import psycopg2 as pg
from utils import *
import signal
from papermage.recipes import CoreRecipe

from dotenv import load_dotenv
load_dotenv()

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

recipe = CoreRecipe()

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

## ---- UTILITY FUNCTIONS ---- ##

def does_file_exist(file_id : str) -> bool:
    """Check if a file with the given ID exists in the database"""
    cursor.execute("SELECT filename FROM papers WHERE id = %s", (file_id,))
    result = cursor.fetchone()
    return result is not None
    
def save_file_to_db(file_id: str, file_name: str) -> None:
    """Save the file to the database. Raises an exception if unsuccessful."""
    cursor.execute("INSERT INTO papers (id, filename) VALUES (%s, %s)", (file_id, file_name))
    conn.commit()

def save_file(file_id : str, file_contents : bytes) -> None:
    """Save the file to the filesystem inside `tmp/` folder as a PDF"""
    if not os.path.exists("tmp/"):
        os.mkdir("tmp/")
    with open(os.path.join('tmp', f"{file_id}.pdf"), "wb") as f:
         f.write(file_contents)
    
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

    try:
        if does_file_exist(file_id):
            print(f"File {file_id} already processed.")
            return JSONResponse(content={"status": "File already processed."}, status_code=409)
    except pg.DatabaseError as e:
        print(f"Error checking for existing file: {e}")
        return JSONResponse(content={"status": "Error checking file in DB."}, status_code=500)
    
    try:
        save_file_to_db(file_id, file.filename)
        print(f"File {file_id} - {file.filename} Inserted into DB")
    except pg.DatabaseError as e:
        print(f"Error saving file: {e}")
        return JSONResponse(content={"status": "Error saving file."}, status_code=500)
    
    try:
        save_file(file_id, file_contents)
        print(f"File {file_id} - {file.filename} Saved to filesystem")
    except OSError as e:
        print(f"Error saving file: {e}")
        return JSONResponse(content={"status": "Server error: retry."}, status_code=500)

    # process the file
    doc = recipe.run(os.path.join('data', f"{file_id}.pdf"))
    markdown_content = process_document(doc)
        
    return {"status": "ok"}