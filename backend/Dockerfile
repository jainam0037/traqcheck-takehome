FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# system deps for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# make entrypoint executable
RUN chmod +x /app/entrypoint.sh

ENV DJANGO_SETTINGS_MODULE=core.settings

EXPOSE 8000
CMD ["bash", "entrypoint.sh"]