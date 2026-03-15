# 🧬 BAKTA LOCAL PLATFORM

> **Desenvolvido por Rui Lima** - PUC Minas

[![Bakta](https://img.shields.io/badge/Bakta-1.9.4-blue.svg)](https://github.com/oschwengers/bakta)
[![Python](https://img.shields.io/badge/Python-3.10-green.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-orange.svg)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-GPLv3-purple.svg)](LICENSE)

> **Interface web moderna e intuitiva para anotação genômica bacteriana** utilizando [Bakta](https://github.com/oschwengers/bakta) - a ferramenta mais rápida e precisa para anotação de genomas.

![PUC Minas](https://img.shields.io/badge/PUC-Minas-blue?style=for-the-badge&logo=graduation-cap)

---

## 📖 Sumário

- [Visão Geral](#-visão-geral)
- [Funcionalidades](#-funcionalidades)
- [Screenshots](#-screenshots)
- [Quick Start](#-quick-start)
- [Instalação](#-instalação)
- [Uso](#-uso)
- [Arquitetura](#-arquitetura)
- [API](#-api)
- [Deploy](#-deploy)
- [Troubleshooting](#-troubleshooting)
- [Contribuição](#-contribuição)

---

## 🎯 Visão Geral

O **Bakta Local Platform** é uma plataforma completa para anotação de genomas bacterianos, desenvolvida como projeto acadêmico da Pontifícia Universidade Católica de Minas Gerais (PUC Minas).

### 🚀 Por que Bakta?

| Característica | Bakta | Prokka | RAST |
|----------------|-------|--------|------|
| **Velocidade** | 🚀 ~10x mais rápido | Moderado | Lento |
| **Precisão** | ⭐⭐⭐⭐⭐ Excelente | ⭐⭐⭐⭐ Boa | ⭐⭐⭐ Regular |
| **Padrões** | NCBI + INSDC | GenBank | Proprietário |
| **Database** | AMRFinder+, COG | UniProt | SEED |
| **Manutenção** | ✅ Ativo (2024) | ⚠️ Legado | ✅ Ativo |

### 📊 Recursos Principais

- 🎨 **Interface Web Moderna** - Design responsivo com Bootstrap 5
- 📁 **Upload Drag & Drop** - Arraste arquivos FASTA diretamente
- 📈 **Dashboard em Tempo Real** - Acompanhe o progresso da anotação
- 🧬 **6 Templates NCBI** - Genomas de referência pré-carregados
- 📊 **Visualização Circular** - Representação gráfica do genoma
- 📥 **Download Completo** - GFF3, JSON, FAA, FFN, GenBank
- 🐳 **Docker Ready** - Deploy em minutos
- ⚡ **Async Processing** - Processamento não-bloqueante

---

## ✨ Funcionalidades

### 🔬 Anotação Genômica Completa

```
✅ CDS (Coding Sequences)       → Prodigal
✅ tRNA                         → tRNAscan-SE 2.0
✅ tmRNA                        → Aragorn 1.2
✅ rRNA                         → INFERNAL 1.1
✅ ncRNA                        → INFERNAL + Rfam
✅ CRISPR                       → PILER-CR
✅ oriC/oriV/oriT               → DnaA-based
✅ AMR Genes                    → AMRFinderPlus
✅ Virulence Factors            → VFDB
✅ Secondary Metabolites        → antiSMASH
```

### 📱 Interface Web

| Feature | Descrição |
|---------|-----------|
| 🎨 **Modern UI** | Bootstrap 5 com tema PUC Minas |
| 📤 **Drag & Drop** | Upload intuitivo de arquivos |
| 📊 **Live Progress** | Barra de progresso em tempo real |
| 📋 **Job History** | Histórico completo de anotações |
| 🔍 **Job Details** | Estatísticas detalhadas por job |
| 💾 **Multi-format** | Download em todos os formatos |
| 📱 **Responsive** | Funciona em desktop, tablet e mobile |

---

## 📸 Screenshots

<p align="center">
  <em>Dashboard Principal</em><br>
  <kbd>Lista de templates + Área de upload + Estatísticas</kbd>
</p>

<p align="center">
  <em>Progresso da Anotação</em><br>
  <kbd>Barra de progresso em tempo real com status detalhado</kbd>
</p>

<p align="center">
  <em>Resultados</em><br>
  <kbd>Tabela de jobs com badges de CDS, tRNAs, rRNAs + download</kbd>
</p>

---

## 🚀 Quick Start

### Opção 1: Docker (Recomendado - 5 minutos)

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/pucminas-bakta.git
cd pucminas-bakta/deployment

# 2. Inicie com Docker Compose
docker-compose up --build

# 3. Acesse no navegador
open http://localhost:5000
```

### Opção 2: Conda (10 minutos)

```bash
# 1. Criar ambiente
conda env create -f environment.yml
conda activate bakta_env

# 2. Baixar database (apenas primeira vez, ~1.3GB)
bakta_db download --type light --output ./bakta-light

# 3. Iniciar servidor
cd backend
python app.py

# 4. Acesse
open http://localhost:5000
```

---

## 📦 Instalação

### Requisitos de Sistema

| Componente | Mínimo | Recomendado |
|------------|--------|-------------|
| **CPU** | 2 cores | 4+ cores |
| **RAM** | 4 GB | 8+ GB |
| **Disco** | 5 GB | 20+ GB |
| **OS** | Linux/Mac/Windows | Linux Ubuntu 22.04 |
| **Network** | Opcional | Para download NCBI |

### Instalação Detalhada

#### 1. Docker

```bash
# Instalar Docker (Ubuntu)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo apt install docker-compose-plugin

# Verificar instalação
docker --version
docker compose version
```

#### 2. Conda

```bash
# Download Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# Recarregar shell
source ~/.bashrc

# Verificar
conda --version
```

#### 3. Configuração do Ambiente

```bash
# Clone
git clone https://github.com/seu-usuario/pucminas-bakta.git
cd pucminas-bakta

# Criar ambiente
conda env create -f environment.yml
conda activate bakta_env

# Verificar Bakta
bakta --version

# Baixar database
bakta_db download --type light --output ./bakta-light

# Preparar diretórios
mkdir -p resultados data/uploads
python data/download_templates.py --output data/templates --dummy
```

---

## 💻 Uso

### Interface Web

1. **Acesse** http://localhost:5000
2. **Escolha uma opção:**
   - 🧬 Selecione um **template** de genoma (E. coli, B. subtilis, etc.)
   - 📤 Ou **faça upload** de seu próprio arquivo FASTA
3. **Configure** o prefixo para os arquivos de saída (opcional)
4. **Clique em "Iniciar Anotação"**
5. **Acompanhe** o progresso em tempo real
6. **Visualize e baixe** os resultados quando concluído

### Linha de Comando

```bash
# Usar o pipeline diretamente
python backend/pipeline.py \
  --db ./bakta-light \
  --output ./resultados \
  --threads 4 \
  ./data/templates/ecoli_k12.fasta

# Listar jobs anteriores
python backend/pipeline.py --list-jobs
```

### API REST

```bash
# Verificar status
curl http://localhost:5000/api/status

# Upload de arquivo
curl -X POST -F "file=@genome.fasta" http://localhost:5000/api/upload

# Iniciar anotação
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"source":"upload","filename":"20260314_235645_genome.fasta"}' \
  http://localhost:5000/api/annotate
```

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENTE (Browser)                        │
│              HTML5 + Bootstrap 5 + JavaScript (ES6+)             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SERVIDOR FLASK (Python)                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  API REST (Flask)  │  Pipeline (BaktaPipeline)  │  File IO │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Subprocess
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MOTOR BAKTA (Bioinformática)                  │
│  Prodigal │ tRNAscan-SE │ Aragorn │ INFERNAL │ HMMER │ Diamond  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ARMAZENAMENTO                               │
│  ├─ Bakta DB (~1.3GB)    → Database de anotação                  │
│  ├─ resultados/          → Saída das anotações                   │
│  ├─ data/uploads/        → Uploads de usuários                   │
│  └─ data/templates/      → Templates de genomas                  │
└─────────────────────────────────────────────────────────────────┘
```

### Documentação Completa

📚 Veja [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md) para detalhes completos da arquitetura.

---

## 🔌 API

### Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/status` | GET | Health check |
| `/api/templates` | GET | Listar templates |
| `/api/upload` | POST | Upload FASTA |
| `/api/annotate` | POST | Iniciar anotação |
| `/api/jobs` | GET | Listar jobs |
| `/api/jobs/<id>` | GET | Detalhes do job |
| `/api/jobs/<id>/status` | GET | Status do job |
| `/api/jobs/<id>/files/<type>` | GET | Download arquivo |
| `/api/jobs/<id>` | DELETE | Remover job |
| `/api/stats` | GET | Estatísticas gerais |

📚 Veja [`docs/API.md`](docs/API.md) para documentação completa da API.

---

## 🚀 Deploy

### Docker Compose

```bash
cd deployment
docker-compose up -d
```

### Produção com Nginx

```bash
cd deployment
docker-compose --profile with-nginx up -d
```

### Cloud (AWS/GCP/Azure)

```bash
# Exemplo AWS EC2
docker run -d \
  -p 80:5000 \
  -v /mnt/data/resultados:/app/resultados \
  -v /mnt/data/bakta-db:/app/bakta-light \
  --name puc-bakta \
  pucminas/bakta:latest
```

📚 Veja [`docs/DEPLOY.md`](docs/DEPLOY.md) para guia completo de deploy.

---

## 🧬 Templates Disponíveis

| Organismo | Acesso NCBI | Tamanho |
|-----------|-------------|---------|
| *Escherichia coli* K-12 | NC_000913.3 | ~4.6 Mb |
| *Bacillus subtilis* 168 | NC_000964.3 | ~4.2 Mb |
| *Staphylococcus aureus* | NC_007795.1 | ~2.8 Mb |
| *Pseudomonas aeruginosa* | NC_002516.2 | ~6.3 Mb |
| *Salmonella enterica* | NC_003198.1 | ~4.9 Mb |
| pUC19 Plasmid | L09137.1 | ~2.7 Kb |

---

## 🐛 Troubleshooting

### Problemas Comuns

#### ❌ "Database não encontrado"

```bash
# Solução: Baixar database
bakta_db download --type light --output ./bakta-light
```

#### ❌ "Permission denied"

```bash
# Solução: Corrigir permissões
sudo chown -R $USER:$USER resultados/ data/
```

#### ❌ "Address already in use"

```bash
# Solução: Usar porta diferente
FLASK_RUN_PORT=8080 python backend/app.py
```

#### ❌ "Memory error"

```bash
# Solução: Aumentar memória do Docker
# Editar docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 16G
```

### Mais Ajuda

📚 Veja [`docs/DEPLOY.md#troubleshooting`](docs/DEPLOY.md#troubleshooting) para soluções detalhadas.

---

## 📁 Estrutura do Projeto

```
Bakta/
├── backend/              # API Flask
│   ├── app.py           # Servidor web
│   └── pipeline.py      # Lógica Bakta
├── frontend/            # Interface web
│   ├── index.html
│   └── static/
│       ├── app.js
│       └── styles.css
├── data/                # Dados
│   ├── download_templates.py
│   ├── templates/       # Templates FASTA
│   └── uploads/         # Uploads de usuários
├── deployment/          # Docker
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── entrypoint.sh
├── docs/                # Documentação
│   ├── ARQUITETURA.md
│   ├── API.md
│   └── DEPLOY.md
├── resultados/          # Saída das anotações
├── environment.yml      # Conda environment
└── README.md           # Este arquivo
```

---

## 🤝 Contribuição

Contribuições são bem-vindas! Siga os passos:

1. **Fork** o projeto
2. Crie uma **branch** (`git checkout -b feature/nova-feature`)
3. **Commit** suas mudanças (`git commit -am 'Add nova feature'`)
4. **Push** para a branch (`git push origin feature/nova-feature`)
5. Abra um **Pull Request**

### Diretrizes

- 📝 Siga o estilo de código PEP 8
- 🧪 Adicione testes para novas features
- 📚 Atualize a documentação
- 🐛 Reporte bugs via Issues

---

## 📚 Referências

### Bakta

- [GitHub](https://github.com/oschwengers/bakta)
- [Documentação](https://bakta.readthedocs.io/)
- [Paper](https://doi.org/10.1099/mgen.0.001085)

### Tecnologias

- [Flask](https://flask.palletsprojects.com/)
- [Bootstrap](https://getbootstrap.com/)
- [Docker](https://www.docker.com/)
- [Conda](https://docs.conda.io/)

### Dados

- [NCBI Genomes](https://www.ncbi.nlm.nih.gov/genome/)
- [UniProt](https://www.uniprot.org/)
- [Rfam](https://rfam.org/)

---

## 📝 Citação

Se você usar este projeto em sua pesquisa, por favor cite:

> Este projeto foi desenvolvido por **Rui Lima** como trabalho da disciplina **Algoritmos de Bioinformática** do curso de **Pós-Graduação da PUC Minas**.

```bibtex
@article{schwengers2021bakta,
  title={Bakta: rapid and standardized annotation of bacterial genomes via alignment-free sequence identification},
  author={Schwengers, Oliver and Jelonek, Lukas and Dieckmann, Marius Alan and Beyvers, Sebastian and Blom, Jochen and Goesmann, Alexander},
  journal={Microbial Genomics},
  volume={7},
  number={11},
  pages={000685},
  year={2021},
  publisher={Microbiology Society}
}
```

---

## 📄 Licença

Este projeto é licenciado sob **GPLv3** - veja o arquivo [LICENSE](LICENSE) para detalhes.

O Bakta original também é licenciado sob GPLv3.

---

## 🎓 Sobre

<p align="center">
  <strong>PUC Minas</strong> - Pontifícia Universidade Católica de Minas Gerais<br>
  Pós-Graduação | Disciplina: Algoritmos de Bioinformática<br>
  <br>
  Desenvolvido por Rui Lima como projeto acadêmico para anotação genômica bacteriana
</p>

<p align="center">
  <a href="https://www.pucminas.br">
    <img src="https://www.pucminas.br/posgraduacao/icafes/wp-content/uploads/sites/82/2019/07/logo-puc-minas.png" alt="PUC Minas" width="150">
  </a>
</p>

---

<p align="center">
  Feito com ❤️ em Belo Horizonte, Brasil<br>
  <em>2026 - PUC Minas</em>
</p>
