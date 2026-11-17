FROM python:3.11-slim
RUN useradd -m -u 1000 user
USER user
WORKDIR /home/user/app
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=user . .
# Render provides $PORT; Hugging Face Spaces uses 7860 (the fallback).
CMD ["sh", "-c", "python -m uvicorn app:app --host 0.0.0.0 --port ${PORT:-7860}"]
