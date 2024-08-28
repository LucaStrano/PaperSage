import sys
import os
import requests

if len(sys.argv) < 2:
    print("Usage: python send_documents.py <doc_path>")
    sys.exit(1)

path = sys.argv[1]
docs = []

# check if path is a directory
if os.path.isdir(path):
    print("Path is a directory")
    docs.extend([os.path.join(path, f) \
                 for f in os.listdir(path) \
                 if f.endswith('.pdf')])
elif path.endswith('.pdf'):
    docs.append(path)

for doc in docs:
    # send the document with a POST request
    filename = os.path.basename(doc)
    doc_contents = open(doc, 'rb').read()
    file = {"file": (filename, doc_contents)}
    print(f"📄 Sending {filename} to PaperMage Service. This might take a while...")
    try:
        res = requests.post("http://localhost:8000/process", files=file)
    except requests.exceptions.RequestException as e:
        print(f"❌ Request to PaperMage Service Failed.")
        sys.exit(1)
    if res.status_code == 200:
        print(f"✅ {doc} Processed Successfully!")
    else:
        print(f"❌ Error : {res.status_code} - {res.text}")