FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml LICENSE README.md ./
COPY ragmate/ ragmate/
RUN pip install --no-cache-dir .

RUN mkdir -p /app/chroma_data /app/uploads

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["uvicorn", "ragmate.main:app", "--host", "0.0.0.0", "--port", "8000"]
