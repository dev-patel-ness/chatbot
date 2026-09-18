# Backend image for the FastAPI chat API and mock actions API (architecture.md §18).
# Playwright browsers are intentionally NOT installed here — ingestion (Stage 1) runs
# as an offline CLI on the host/dev machine, not inside this request-serving image.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8080"]
