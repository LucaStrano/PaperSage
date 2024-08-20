# This runs on port 8000

from fastapi import FastAPI, UploadFile
import os

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/process")
async def process(file: UploadFile):
    
    # Read the contents of the uploaded file
    file_contents = await file.read()
    print(f"RECEIVED {file.filename}")

    if not os.path.exists("docs/"):
        os.makedirs("docs/")

    with open(f"docs/{file.filename}", "wb") as f:
        f.write(file_contents)

    return {"status": "ok"}