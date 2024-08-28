# This runs on port 8000

from fastapi import FastAPI, UploadFile
import os
import psycopg2 as pg
from utils import *
import signal

# from dotenv import load_dotenv
# load_dotenv()

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
    cursor.close()
    conn.close()
    exit(0)
signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

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

    return {"status": "ok"}