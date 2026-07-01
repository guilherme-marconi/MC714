FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY start.sh .

RUN chmod +x start.sh

# 8000 -> FastAPI (backend) | 8501 -> Streamlit (frontend)
EXPOSE 8000 8501

CMD ["./start.sh"]
