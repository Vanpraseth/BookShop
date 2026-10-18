FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    PORT=8080 \
    BOOKSHOP_DB=/app/data/bookshop.db \
    SEED_CATALOGUE=true

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend
COPY database /app/database
COPY frontend /app/frontend

RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appgroup /app/data

USER appuser
EXPOSE 8080

CMD ["sh", "-c", "exec gunicorn --chdir backend --bind 0.0.0.0:${PORT:-8080} --workers 1 --threads 4 --access-logfile - --error-logfile - server:app"]
