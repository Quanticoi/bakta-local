# Guia de Deploy - Bakta Flow

## Índice

1. [Deploy com Docker](#deploy-com-docker)
2. [Deploy Local](#deploy-local)
3. [Deploy em Produção](#deploy-em-produção)
4. [Troubleshooting](#troubleshooting)

---

## Deploy com Docker

### Requisitos

- Docker 20.10+
- Docker Compose 2.0+
- 8GB RAM disponível
- 10GB espaço em disco

### Quick Start

```bash
# Clone o repositório
git clone <repo-url>
cd Bakta/deployment

# Iniciar
docker-compose up -d

# Verificar logs
docker-compose logs -f

# Acessar
open http://localhost:5000
```

### Comandos Úteis

```bash
# Construir imagem
docker-compose build --no-cache

# Escalar para múltiplas instâncias
docker-compose up -d --scale bakta-app=3

# Parar
docker-compose down

# Limpar tudo (incluindo volumes)
docker-compose down -v

# Executar comando no container
docker-compose exec bakta-app bash

# Ver recursos
docker stats
```

### Com Nginx (Produção)

```bash
# Iniciar com Nginx reverse proxy
docker-compose --profile with-nginx up -d

# Acessar via porta 80
open http://localhost
```

### Configurações

**docker-compose.yml customizado:**

```yaml
version: '3.8'

services:
  bakta-app:
    build:
      context: ..
      dockerfile: deployment/Dockerfile
    ports:
      - "5000:5000"
    volumes:
      - /mnt/data/resultados:/app/resultados
      - /mnt/data/uploads:/app/data/uploads
      - bakta-db:/app/bakta-light
    environment:
      - FLASK_ENV=production
      - BAKTA_DB=/app/bakta-light
    deploy:
      resources:
        limits:
          cpus: '8'
          memory: 16G
    restart: unless-stopped

volumes:
  bakta-db:
    driver: local
```

---

## Deploy Local

### Requisitos

- Python 3.10+
- Conda ou Miniconda
- 8GB RAM
- 5GB espaço para database

### Instalação Passo a Passo

#### 1. Instalar Conda

```bash
# Download Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# Recarregar shell
source ~/.bashrc
```

#### 2. Clonar e Configurar

```bash
git clone <repo-url>
cd Bakta

# Criar ambiente
conda env create -f environment.yml
conda activate bakta_env

# Verificar instalação
bakta --version
```

#### 3. Baixar Database

```bash
# Database light (~1.3GB)
bakta_db download --type light --output ./bakta-light

# Ou database full (~100GB)
# bakta_db download --type full --output ./bakta-full
```

#### 4. Preparar Dados

```bash
# Criar diretórios
mkdir -p resultados data/uploads

# Baixar templates
python data/download_templates.py --output data/templates --dummy
```

#### 5. Iniciar Servidor

```bash
cd backend

# Modo desenvolvimento
python app.py

# Modo produção
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## Deploy em Produção

### 1. Configuração de Segurança

#### Firewall

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# iptables
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 5000 -j DROP  # Bloquear acesso direto
```

#### Nginx Config

```nginx
# /etc/nginx/sites-available/bakta
server {
    listen 80;
    server_name seu-dominio.com;
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Ativar
sudo ln -s /etc/nginx/sites-available/bakta /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### HTTPS com Certbot

```bash
# Instalar certbot
sudo apt install certbot python3-certbot-nginx

# Obter certificado
sudo certbot --nginx -d seu-dominio.com

# Auto-renewal
sudo certbot renew --dry-run
```

### 2. Systemd Service

```ini
# /etc/systemd/system/bakta.service
[Unit]
Description=Bakta Flow
After=network.target

[Service]
User=bakta
Group=bakta
WorkingDirectory=/opt/bakta/backend
Environment="PATH=/opt/conda/envs/bakta_env/bin"
Environment="BAKTA_DB=/opt/bakta/bakta-light"
Environment="FLASK_ENV=production"
ExecStart=/opt/conda/envs/bakta_env/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
# Configurar
sudo useradd -r -s /bin/false bakta
sudo mkdir -p /opt/bakta
sudo cp -r . /opt/bakta/
sudo chown -R bakta:bakta /opt/bakta

# Iniciar
sudo systemctl daemon-reload
sudo systemctl enable bakta
sudo systemctl start bakta
sudo systemctl status bakta
```

### 3. Monitoramento

#### Logrotate

```bash
# /etc/logrotate.d/bakta
/opt/bakta/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 bakta bakta
}
```

#### Prometheus (opcional)

```python
# Adicionar ao app.py
from prometheus_flask_exporter import PrometheusMetrics

metrics = PrometheusMetrics(app)
```

### 4. Backup

```bash
#!/bin/bash
# /opt/bakta/backup.sh

BACKUP_DIR="/backup/bakta/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup resultados
tar -czf $BACKUP_DIR/resultados.tar.gz /opt/bakta/resultados

# Backup database (se personalizado)
# tar -czf $BACKUP_DIR/bakta-db.tar.gz /opt/bakta/bakta-light

# Limpar backups antigos (> 30 dias)
find /backup/bakta -type d -mtime +30 -exec rm -rf {} \;
```

```bash
# Cron job
0 2 * * * /opt/bakta/backup.sh
```

---

## Cloud Deployment

### AWS EC2

```bash
# 1. Launch EC2 instance (t2.xlarge recomendado)
# 2. Security Group: abrir portas 22, 80, 443

# Conectar
ssh -i key.pem ubuntu@<ec2-ip>

# Instalar Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu

# Deploy
git clone <repo>
cd Bakta/deployment
docker-compose up -d
```

### Google Cloud Run

```yaml
# cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/bakta', '-f', 'deployment/Dockerfile', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/bakta']
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'bakta'
      - '--image'
      - 'gcr.io/$PROJECT_ID/bakta'
      - '--platform'
      - 'managed'
      - '--region'
      - 'us-central1'
      - '--memory'
      - '8Gi'
      - '--cpu'
      - '4'
```

---

## Troubleshooting

### Problemas Comuns

#### 1. Database não encontrado

```bash
# Sintoma: Erro "Database not found"
# Solução:
bakta_db download --type light --output ./bakta-light

# Ou no Docker:
docker-compose exec bakta-app bakta_db download --type light --output /app/bakta-light
```

#### 2. Permissões de arquivo

```bash
# Sintoma: "Permission denied"
# Solução:
sudo chown -R $USER:$USER resultados/ data/
chmod 755 resultados/ data/
```

#### 3. Porta ocupada

```bash
# Sintoma: "Address already in use"
# Solução:
sudo lsof -i :5000
sudo kill -9 <PID>

# Ou usar porta diferente:
FLASK_RUN_PORT=8080 python app.py
```

#### 4. Memory Error

```bash
# Sintoma: Processo morto durante anotação
# Solução: Aumentar memória do Docker
docker-compose down
# Editar docker-compose.yml, aumentar memory limit
docker-compose up -d
```

#### 5. CORS Errors

```bash
# Sintoma: "CORS policy" no navegador
# Solução: Verificar configuração Flask-CORS
# Em backend/app.py:
CORS(app, origins=['https://seu-dominio.com'])
```

### Debug Mode

```bash
# Ativar debug
docker-compose exec bakta-app bash
export FLASK_DEBUG=1
python backend/app.py

# Ver logs detalhados
docker-compose logs -f --tail=100
```

### Health Check

```bash
# Testar API
curl http://localhost:5000/api/status

# Testar Bakta
docker-compose exec bakta-app bakta --version

# Testar database
docker-compose exec bakta-app ls -la /app/bakta-light
```

---

## Checklist de Produção

- [ ] HTTPS configurado
- [ ] Firewall ativo
- [ ] Backups automatizados
- [ ] Monitoramento configurado
- [ ] Logs rotacionados
- [ ] Recursos suficientes (RAM/CPU)
- [ ] Database baixado
- [ ] Teste de carga realizado
- [ ] Documentação atualizada
- [ ] Contatos de emergência definidos
