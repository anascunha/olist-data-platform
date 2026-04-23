FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema necessárias para compilação e download
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependências Python e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Criar usuário não-root por segurança
RUN useradd -m appuser && chown -R appuser /app
USER appuser

CMD ["bash"]
