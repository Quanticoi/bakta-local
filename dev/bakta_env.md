# Bakta Flow Environment Requirements

## 📋 Visão Geral do Projeto

Este documento define os requisitos técnicos para criação de um ambiente completo de estudos da biblioteca **Bakta** - uma ferramenta moderna e rápida para anotação genômica de bactérias.

**Referência Oficial:** https://github.com/oschwengers/bakta

---

## 🎯 Objetivos

1. Preparar ambiente Conda isolado para o Bakta
2. Instalar e configurar a ferramenta Bakta com database light
3. Criar pipeline de execução automatizado
4. Desenvolver interface web elegante (Bakta Flow)
5. Implementar visualização de resultados com BaktaPlot
6. Containerizar a aplicação com Docker

---

## 📁 Estrutura de Diretórios

```
Bakta/
├── dev/
│   └── bakta_env.md              # Este documento
├── data/                          # Templates de genomas (NCBI)
├── backend/                       # Scripts do pipeline
├── frontend/                      # Interface web
├── resultados/                    # Saídas das anotações
├── deployment/                    # Docker e Compose
└── environment.yml                # Conda environment
```

---

## 🔧 Requisitos Técnicos

### 1. Ambiente Conda

**Ferramenta:** Miniconda ou Conda

```yaml
# environment.yml
name: bakta_env
channels:
  - bioconda
  - conda-forge
  - defaults
dependencies:
  - python=3.10
  - bakta
  - baktaplot
  - pip
  - pip:
    - flask
    - flask-cors
    - requests
```

### 2. Database Bakta

**Opção:** Versão Light (1.3GB) - adequada para estudos

```bash
# Download database light
bakta_db download --type light --output ./bakta-light
```

### 3. Instalação Bakta

```bash
# Criar ambiente
conda env create -f environment.yml
conda activate bakta_env

# Verificar instalação
bakta --version
```

---

## 🧬 Pipeline de Execução (Backend)

### Script Principal: `backend/pipeline.py`

**Funcionalidades:**
- Aceitar arquivo FASTA como input
- Executar anotação com Bakta
- Parâmetros padrão:
  - `--db`: caminho para database light
  - `--meta`: modo metagenoma (mais tolerante)
  - `--threads`: 4
  - `--output`: ./resultados/{nome_job}
  - `--prefix`: nome do arquivo

**Output:**
- Estrutura JSON para consumo do frontend
- Arquivos .gff3, .faa, .ffn, .json

---

## 🎨 Frontend (Bakta Flow)

### Tecnologias:
- **Framework:** Flask (Python)
- **UI:** HTML5 + CSS3 + JavaScript
- **Visualização:** BaktaPlot (embedado)
- **Estilo:** Bootstrap 5 ou Tailwind CSS

### Funcionalidades:

1. **Página Principal:**
   - Header: "Bakta Flow"
   - Seletor de templates (pasta `data/`)
   - Upload de arquivo FASTA customizado
   - Botão "Executar Anotação"

2. **Dashboard de Resultados:**
   - Visualizador BaktaPlot integrado
   - Área de estatísticas:
     - Número de CDS
     - Número de genes
     - Número de RNAs
     - GC content
     - Tamanho do genoma
   - Download de arquivos

3. **Histórico:**
   - Lista de jobs executados
   - Status (em andamento, concluído, erro)

---

## 📊 Visualização (BaktaPlot)

**Integração:**
- Embedar visualização SVG/circular do genoma
- Exibir features (CDS, tRNA, rRNA)
- Cores por tipo de feature

---

## 🐳 Docker Deployment

### Arquivos:
- `deployment/Dockerfile`
- `deployment/docker-compose.yml`
- `deployment/entrypoint.sh`

### Container:
- Base: `continuumio/miniconda3`
- Instalação do Bakta
- Download database light
- Expor porta 5000 (Flask)
- Volume para `data/` e `resultados/`

---

## 📦 Dados de Exemplo (NCBI)

### Templates na pasta `data/`:
1. **Escherichia coli** - plasmídeo pUC19
2. **Bacillus subtilis** - genoma reduzido
3. **Staphylococcus aureus** - plasmídeo

**Formato:** FASTA (.fna ou .fasta)

---

## 🚀 Comandos de Execução

### Desenvolvimento:
```bash
conda activate bakta_env
python backend/app.py
```

### Docker:
```bash
cd deployment
docker-compose up --build
```

### Bakta Manual:
```bash
bakta --db ./bakta-light \
      --meta \
      --threads 4 \
      --output ./resultados/teste \
      --prefix genoma \
      ./data/exemplo.fasta
```

---

## 📋 Checklist de Implementação

- [ ] Criar estrutura de pastas
- [ ] Configurar environment.yml
- [ ] Criar backend/pipeline.py
- [ ] Criar backend/app.py (API Flask)
- [ ] Baixar templates NCBI
- [ ] Desenvolver frontend/index.html
- [ ] Desenvolver frontend/app.js
- [ ] Integrar BaktaPlot
- [ ] Criar Dockerfile
- [ ] Criar docker-compose.yml
- [ ] Criar entrypoint.sh
- [ ] Testar pipeline completo

---

## 📚 Referências

1. GitHub Bakta: https://github.com/oschwengers/bakta
2. Documentação: https://bakta.readthedocs.io/
3. BaktaPlot: https://github.com/oschwengers/bakta/tree/main/scripts
4. NCBI Genomes: https://www.ncbi.nlm.nih.gov/genome/

---

**Data:** 2026-03-14  
**Versão:** 1.0  
**Autor:** PUC Minas - Projeto Bakta
