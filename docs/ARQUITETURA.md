# Arquitetura do Bakta Flow

## Visão Geral da Arquitetura

O Bakta Flow é uma aplicação web full-stack para anotação genômica bacteriana, construída com uma arquitetura em camadas que separa claramente as responsabilidades de frontend, backend e processamento de dados.

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENTE (Browser)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Interface Web (HTML5 + Bootstrap 5 + JavaScript)         │  │
│  │  - Upload de arquivos (drag & drop)                       │  │
│  │  - Dashboard de monitoramento                             │  │
│  │  - Visualização de resultados                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SERVIDOR FLASK (Python)                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  API REST (Flask + Flask-CORS)                            │  │
│  │  ├─ /api/status      → Health check                       │  │
│  │  ├─ /api/templates   → Listar templates                   │  │
│  │  ├─ /api/upload      → Upload de FASTA                    │  │
│  │  ├─ /api/annotate    → Iniciar anotação                   │  │
│  │  ├─ /api/jobs        → Gerenciar jobs                     │  │
│  │  └─ /api/jobs/<id>   → Detalhes do job                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Pipeline Bakta (BaktaPipeline)                           │  │
│  │  - Validação de inputs                                    │  │
│  │  - Execução assíncrona (Threading)                        │  │
│  │  - Parse de resultados JSON/GFF3                          │  │
│  │  - Persistência em arquivo                                │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Subprocess / CLI
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MOTOR DE ANOTAÇÃO (Bakta)                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Bakta CLI (Bioinformática)                               │  │
│  │  ├─ Prodigal      → Predição de CDS                       │  │
│  │  ├─ tRNAscan-SE   → Detecção de tRNA                     │  │
│  │  ├─ Aragorn       → Detecção de tmRNA                    │  │
│  │  ├─ Infernal      → RNA não-codificante                  │  │
│  │  ├─ HMMER         → Domínios proteicos                   │  │
│  │  ├─ Diamond       → Homologia proteica                   │  │
│  │  └─ AMRFinderPlus → Resistência antimicrobiana           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ARMAZENAMENTO                               │
│  ├─ Bakta DB          → Database de anotação (~1.3GB)          │
│  ├─ resultados/       → Saída das anotações                    │
│  ├─ data/uploads/     → Uploads de usuários                    │
│  └─ data/templates/   → Templates de genomas                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Diagrama de Componentes

```
                    ┌─────────────────────────────────────┐
                    │         Usuário                     │
                    └──────────────┬──────────────────────┘
                                   │
                                   │ HTTPS (80/443)
                                   ▼
    ┌──────────────────────────────────────────────────────────────┐
    │                      Nginx (Opcional)                        │
    │              (Reverse Proxy + Load Balancer)                 │
    └──────────────────────────────┬───────────────────────────────┘
                                   │
                                   │ HTTP (5000)
                                   ▼
    ┌──────────────────────────────────────────────────────────────┐
    │                    Flask Application                         │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
    │  │   Routes     │  │   Services   │  │   Models     │       │
    │  │  (Views)     │──│  (Pipeline)  │──│   (File IO)  │       │
    │  └──────────────┘  └──────────────┘  └──────────────┘       │
    └──────────────────────────────┬───────────────────────────────┘
                                   │
                                   ▼
    ┌──────────────────────────────────────────────────────────────┐
    │                    Data Layer                                │
    │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
    │  │  JSON    │ │  GFF3    │ │  FASTA   │ │  FAA/FFN │       │
    │  │ Results  │ │ Annotations│ │ Sequences│ │ Features │       │
    │  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
    └──────────────────────────────────────────────────────────────┘
```

---

## Fluxo de Dados

### 1. Upload e Início de Anotação

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ Browser │────▶│  Flask  │────▶│  Save   │────▶│   Job   │
│         │     │  Upload │     │  File   │     │  Queue  │
└─────────┘     └─────────┘     └─────────┘     └────┬────┘
                                                      │
┌─────────┐     ┌─────────┐     ┌─────────┐          │
│ Browser │◀────│  Poll   │◀────│  Status │◀─────────┤
│ (UI)    │     │ Status  │     │  Update │          │
└─────────┘     └─────────┘     └─────────┘          │
                                                      ▼
                                               ┌─────────┐
                                               │  Bakta  │
                                               │   CLI   │
                                               └────┬────┘
                                                    │
                                               ┌────┴────┐
                                               │ Results │
                                               │  JSON   │
                                               └─────────┘
```

### 2. Sequência de Processamento

```
[Input FASTA]
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│  1. VALIDAÇÃO                                               │
│     - Formato FASTA                                         │
│     - Tamanho (< 100MB)                                     │
│     - Charset válido                                        │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  2. PIPELINE BAKTA                                          │
│     ├─ Replicon Analysis   (tamanho, GC%, contigs)          │
│     ├─ CDS Prediction      (Prodigal)                       │
│     ├─ Protein Annotation  (Diamond + HMMER)                │
│     ├─ RNA Detection       (tRNAscan-SE, Aragorn, Infernal) │
│     ├─ CRISPR Detection    (PILER-CR)                       │
│     └─ AMR/VF Detection    (AMRFinderPlus)                  │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  3. OUTPUT GENERATION                                       │
│     ├─ .json → Resultados estruturados                      │
│     ├─ .gff3 → Anotações no formato padrão                  │
│     ├─ .faa  → Sequências de proteínas                      │
│     ├─ .ffn  → Sequências de genes                          │
│     ├─ .fna  → Sequências nucleotídicas                     │
│     ├─ .gbff → Formato GenBank                              │
│     └─ .txt  → Resumo legível                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Modelo de Dados

### Job Summary (JSON)

```json
{
  "job_id": "20260314_235645_a1b2c3d4",
  "status": "completed",
  "prefix": "ecoli_sample",
  "output_dir": "/app/resultados/20260314_235645_a1b2c3d4",
  "files": {
    "json": {
      "path": ".../ecoli_sample.json",
      "description": "Resultados JSON",
      "size": 154320
    },
    "gff3": { "path": "...", "description": "Anotação GFF3", "size": 85420 },
    "faa":  { "path": "...", "description": "Proteínas",     "size": 124500 },
    "ffn":  { "path": "...", "description": "Features DNA",  "size": 98700 }
  },
  "stats": {
    "genome_size": 4639675,
    "gc_content": 50.79,
    "n_contigs": 1,
    "n50": 4639675,
    "cds": 4243,
    "genes": 4243,
    "trnas": 89,
    "rrnas": 22,
    "ncrnas": 15,
    "tmrnas": 1
  }
}
```

### Bakta JSON Output (parcial)

```json
{
  "version": "1.9.4",
  "genome": {
    "genus": "Escherichia",
    "species": "coli",
    "strain": "K-12",
    "complete": true
  },
  "stats": {
    "genome_size": 4639675,
    "gc": 50.79,
    "n_contigs": 1,
    "n50": 4639675
  },
  "features": [
    {
      "type": "cds",
      "contig": "contig_1",
      "start": 190,
      "stop": 255,
      "strand": "+",
      "gene": "thrL",
      "product": "thr operon leader peptide",
      "db_xrefs": ["UniProtKB:P0AD86"]
    }
  ]
}
```

---

## Padrões de Design

### 1. MVC (Model-View-Controller)

| Camada | Componente | Responsabilidade |
|--------|------------|------------------|
| **Model** | `BaktaPipeline`, File I/O | Dados e lógica de negócio |
| **View** | `index.html`, `app.js` | Interface do usuário |
| **Controller** | Flask Routes (`app.py`) | Receber requisições, chamar Model, retornar View |

### 2. Repository Pattern

```python
class BaktaPipeline:
    def list_jobs() -> List[Dict]      # Read from filesystem
    def get_job(id) -> Dict            # Read specific job
    def create_job(data) -> Dict       # Initialize new job
    def delete_job(id) -> bool         # Remove job
```

### 3. Async Processing

```python
# Thread para execução não-bloqueante
def run_annotation_async(job_id, fasta_path, prefix):
    thread = Thread(target=_execute_bakta, args=(...))
    thread.daemon = True
    thread.start()
```

---

## Tecnologias e Dependências

### Backend

| Tecnologia | Versão | Uso |
|------------|--------|-----|
| Python | 3.10 | Runtime principal |
| Flask | 2.3+ | Framework web |
| Flask-CORS | 4.0+ | Cross-origin requests |
| Werkzeug | 2.3+ | WSGI utilities |
| Gunicorn | 21.0+ | Production server |

### Bioinformática

| Ferramenta | Versão | Função |
|------------|--------|--------|
| Bakta | 1.9+ | Anotação genômica |
| Prodigal | 2.6+ | Predição de genes |
| tRNAscan-SE | 2.0+ | tRNA detection |
| Aragorn | 1.2+ | tmRNA detection |
| Infernal | 1.1+ | ncRNA detection |
| HMMER | 3.3+ | Profile HMMs |
| Diamond | 2.1+ | Protein alignment |
| AMRFinderPlus | 3.11+ | AMR genes |

### Frontend

| Tecnologia | Versão | Uso |
|------------|--------|-----|
| Bootstrap | 5.3 | UI Framework |
| Bootstrap Icons | 1.11 | Ícones |
| Vanilla JS | ES6+ | Lógica cliente |
| Fetch API | Native | HTTP requests |

---

## Segurança

### Medidas Implementadas

1. **Validação de Upload**
   ```python
   ALLOWED_EXTENSIONS = {'fasta', 'fna', 'fa', 'fas'}
   MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
   ```

2. **Secure Filenames**
   ```python
   from werkzeug.utils import secure_filename
   filename = secure_filename(file.filename)
   ```

3. **CORS Control**
   ```python
   CORS(app)  # Restrict in production
   ```

4. **Path Traversal Protection**
   ```python
   # All paths resolved via Pathlib
   job_dir = self.output_dir / secure_filename(job_id)
   ```

---

## Escalabilidade

### Estratégias

| Aspecto | Estratégia | Implementação |
|---------|-----------|---------------|
| **Horizontal** | Múltiplas instâncias | Docker Swarm / Kubernetes |
| **Vertical** | Mais recursos | Ajuste de threads do Bakta |
| **Caching** | Resultados cacheados | Redis para job status |
| **Queue** | Fila de processamento | Celery + RabbitMQ (futuro) |

### Docker Compose Scaling

```yaml
# docker-compose.yml (produção)
services:
  bakta-app:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '8'
          memory: 16G
```

---

## Monitoramento

### Health Checks

```python
@app.route('/api/status')
def api_status():
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    })
```

### Métricas

| Métrica | Endpoint | Descrição |
|---------|----------|-----------|
| Jobs ativos | `/api/stats` | Total, completed, errors |
| Performance | Logs | Tempo de execução |
| Recursos | Docker Stats | CPU, memória, disco |

---

## Referências

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Bakta GitHub](https://github.com/oschwengers/bakta)
- [GFF3 Specification](https://github.com/The-Sequence-Ontology/Specifications/blob/master/gff3.md)
- [Bootstrap 5 Docs](https://getbootstrap.com/docs/5.3/)
