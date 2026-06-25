FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential python3-dev curl && rm -rf /var/lib/apt/lists/*

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

ENV PATH="/root/.cargo/bin:${PATH}"

COPY requirements-lock.txt .
RUN pip install --no-cache-dir -r requirements-lock.txt

COPY pyproject.toml LICENSE README.md ./
COPY ragmate/ ragmate/
RUN pip install --no-cache-dir --no-deps .

RUN mkdir -p /app/chroma_data /app/uploads \
    && useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app

USER appuser

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 7860

CMD ["uvicorn", "ragmate.main:app", "--host", "0.0.0.0", "--port", "7860"]
