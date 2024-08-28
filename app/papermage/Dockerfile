FROM python:3.9-slim

WORKDIR app/

COPY requirements.txt .
COPY app.py .
COPY utils.py .

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    build-essential \
    libffi-dev \
    libbz2-dev \
    liblzma-dev \
    libsqlite3-dev \
    libncurses5-dev \
    libgdbm-dev \
    zlib1g-dev \
    libreadline-dev \
    libpcap-dev \
    curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "app:app", "--port", "8000", "--host", "0.0.0.0"]
