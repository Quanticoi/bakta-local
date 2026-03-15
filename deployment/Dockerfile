# Bakta Flow Docker Image
# Imagem Docker completa para anotação genômica com Bakta

FROM continuumio/miniconda3:latest

LABEL maintainer="PUC Minas"
LABEL description="Bakta - Bacterial Genome Annotation Tool"
LABEL version="1.0.0"

# Evitar prompts interativos
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    curl \
    git \
    unzip \
    gzip \
    && rm -rf /var/lib/apt/lists/*

# Configurar diretório de trabalho
WORKDIR /app

# Copiar arquivo de ambiente conda
COPY environment.yml /app/environment.yml

# Criar ambiente Conda e instalar dependências
RUN conda env create -f /app/environment.yml && \
    conda clean -afy

# Ativar ambiente no PATH
ENV PATH=/opt/conda/envs/bakta_env/bin:$PATH

# Criar diretórios necessários
RUN mkdir -p /app/data/uploads /app/data/templates /app/resultados /app/bakta-light

# Copiar código da aplicação
COPY backend /app/backend
COPY frontend /app/frontend

# Script para download do database (será executado no entrypoint se necessário)
RUN echo '#!/bin/bash\n\
    if [ ! -d "/app/bakta-light" ] || [ -z "$(ls -A /app/bakta-light)" ]; then\n\
    echo "Downloading Bakta database (light version)..."\n\
    bakta_db download --type light --output /app/bakta-light\n\
    fi' > /app/check_db.sh && chmod +x /app/check_db.sh

# Expor porta
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/api/status || exit 1

# Entrypoint
COPY deployment/entrypoint.sh /app/entrypoint.sh
RUN sed -i 's/\r$//' /app/entrypoint.sh && chmod +x /app/entrypoint.sh

ENTRYPOINT ["bash", "/app/entrypoint.sh"]
