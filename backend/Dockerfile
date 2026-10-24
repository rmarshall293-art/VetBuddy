# Build from the repository root (the API reads data/reference):
#   docker build -f backend/Dockerfile .
FROM python:3.13-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 VB_REFERENCE_DIR=/app/data/reference
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY backend/migrations ./migrations
COPY data/reference ./data/reference
RUN useradd --system --uid 10001 vetbuddy
USER vetbuddy
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
