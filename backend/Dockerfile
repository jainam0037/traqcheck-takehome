FROM python:3.11-slim

WORKDIR /app

# pg_isready + build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc build-essential libpq-dev postgresql-client \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
RUN chmod +x /app/entrypoint.sh
