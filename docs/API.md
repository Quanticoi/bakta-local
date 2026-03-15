# Documentação da API - Bakta Flow

## Base URL

```
Desenvolvimento: http://localhost:5000
Produção: https://seu-dominio.com
```

## Autenticação

Atualmente a API não requer autenticação (uso em rede interna/fechada).

## Content-Type

Todas as requisições e respostas usam `application/json`, exceto upload de arquivos (`multipart/form-data`).

---

## Endpoints

### 1. Status da API

**Verificar se a API está funcionando.**

```http
GET /api/status
```

**Resposta (200 OK):**
```json
{
  "status": "ok",
  "service": "Bakta Flow API",
  "version": "1.0.0",
  "timestamp": "2026-03-14T23:45:00.000000"
}
```

---

### 2. Listar Templates

**Obter lista de templates de genomas disponíveis.**

```http
GET /api/templates
```

**Resposta (200 OK):**
```json
{
  "templates": [
    {
      "id": "ecoli_k12",
      "name": "ecoli_k12.fasta",
      "size": 4639675,
      "path": "/app/data/templates/ecoli_k12.fasta"
    },
    {
      "id": "bsubtilis",
      "name": "bsubtilis.fasta", 
      "size": 4215606,
      "path": "/app/data/templates/bsubtilis.fasta"
    }
  ]
}
```

---

### 3. Upload de Arquivo

**Fazer upload de arquivo FASTA.**

```http
POST /api/upload
Content-Type: multipart/form-data
```

**Parâmetros:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `file` | File | Arquivo FASTA (.fasta, .fna, .fa, .fas) |

**Resposta (200 OK):**
```json
{
  "success": true,
  "filename": "20260314_235645_sample.fasta",
  "original_name": "sample.fasta",
  "path": "/app/data/uploads/20260314_235645_sample.fasta",
  "size": 154320
}
```

**Erros:**
- `400` - Nenhum arquivo enviado
- `400` - Tipo de arquivo não permitido
- `413` - Arquivo muito grande (> 100MB)

---

### 4. Iniciar Anotação

**Iniciar processo de anotação genômica.**

```http
POST /api/annotate
Content-Type: application/json
```

**Body:**
```json
{
  "source": "upload",
  "filename": "20260314_235645_sample.fasta",
  "prefix": "sample_genome"
}
```

**Parâmetros:**
| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `source` | string | Sim | Origem: `"upload"` ou `"template"` |
| `filename` | string | Sim | Nome do arquivo |
| `prefix` | string | Não | Prefixo para arquivos de saída |

**Resposta (200 OK):**
```json
{
  "success": true,
  "job_id": "20260314_235645_a1b2c3d4",
  "status": "started",
  "message": "Anotação iniciada"
}
```

**Erros:**
- `400` - Dados não fornecidos
- `404` - Arquivo não encontrado

---

### 5. Listar Jobs

**Obter lista de todos os jobs executados.**

```http
GET /api/jobs
```

**Resposta (200 OK):**
```json
{
  "jobs": [
    {
      "job_id": "20260314_235645_a1b2c3d4",
      "status": "completed",
      "prefix": "ecoli_sample",
      "output_dir": "/app/resultados/20260314_235645_a1b2c3d4",
      "stats": {
        "genome_size": 4639675,
        "gc_content": 50.79,
        "cds": 4243,
        "trnas": 89,
        "rrnas": 22
      }
    }
  ],
  "total": 1
}
```

---

### 6. Obter Job

**Obter detalhes de um job específico.**

```http
GET /api/jobs/{job_id}
```

**Parâmetros:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `job_id` | string | ID do job |

**Resposta (200 OK):**
```json
{
  "job_id": "20260314_235645_a1b2c3d4",
  "status": "completed",
  "output_dir": "/app/resultados/20260314_235645_a1b2c3d4",
  "prefix": "ecoli_sample",
  "files": {
    "json": {
      "path": ".../ecoli_sample.json",
      "description": "Resultados JSON",
      "size": 154320
    },
    "gff3": {
      "path": ".../ecoli_sample.gff3", 
      "description": "Anotação GFF3",
      "size": 85420
    }
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
    "ncrnas": 15
  }
}
```

**Erros:**
- `404` - Job não encontrado

---

### 7. Status do Job

**Obter status atual de um job (para polling).**

```http
GET /api/jobs/{job_id}/status
```

**Resposta (200 OK) - Em andamento:**
```json
{
  "status": "running",
  "progress": 45,
  "message": "Executando Bakta...",
  "started_at": "2026-03-14T23:56:45.000000"
}
```

**Resposta (200 OK) - Concluído:**
```json
{
  "status": "completed",
  "progress": 100,
  "message": "Anotação concluída!",
  "result": { ... }
}
```

**Resposta (200 OK) - Erro:**
```json
{
  "status": "error",
  "progress": 0,
  "message": "Database não encontrado"
}
```

---

### 8. Download de Arquivo

**Baixar arquivo de resultado.**

```http
GET /api/jobs/{job_id}/files/{file_type}
```

**Parâmetros:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `job_id` | string | ID do job |
| `file_type` | string | Tipo: `json`, `gff3`, `faa`, `ffn`, `fna`, `txt` |

**Resposta:**
- `200` - Arquivo para download (attachment)
- `404` - Arquivo não encontrado

---

### 9. Deletar Job

**Remover um job e seus arquivos.**

```http
DELETE /api/jobs/{job_id}
```

**Resposta (200 OK):**
```json
{
  "success": true,
  "message": "Job removido"
}
```

**Erros:**
- `404` - Job não encontrado

---

### 10. Estatísticas

**Obter estatísticas gerais do sistema.**

```http
GET /api/stats
```

**Resposta (200 OK):**
```json
{
  "total_jobs": 42,
  "completed": 38,
  "errors": 4,
  "total_cds_annotated": 157892
}
```

---

### 11. Verificar Bakta

**Verificar instalação do Bakta e database.**

```http
GET /api/bakta/check
```

**Resposta (200 OK):**
```json
{
  "bakta_installed": true,
  "database_exists": true,
  "database_path": "/app/bakta-light"
}
```

---

## Códigos de Erro

| Código | Descrição |
|--------|-----------|
| `200` | OK - Sucesso |
| `400` | Bad Request - Requisição inválida |
| `404` | Not Found - Recurso não encontrado |
| `413` | Payload Too Large - Arquivo muito grande |
| `500` | Internal Server Error - Erro interno |

---

## Exemplos de Uso

### cURL

```bash
# Verificar status
curl http://localhost:5000/api/status

# Listar templates
curl http://localhost:5000/api/templates

# Upload de arquivo
curl -X POST -F "file=@genome.fasta" http://localhost:5000/api/upload

# Iniciar anotação
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"source":"upload","filename":"20260314_235645_genome.fasta"}' \
  http://localhost:5000/api/annotate

# Verificar status do job
curl http://localhost:5000/api/jobs/20260314_235645_a1b2c3d4/status

# Download de resultado
curl -O http://localhost:5000/api/jobs/20260314_235645_a1b2c3d4/files/gff3
```

### Python

```python
import requests

# Upload
with open('genome.fasta', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/api/upload',
        files={'file': f}
    )
    upload_data = response.json()

# Anotar
response = requests.post(
    'http://localhost:5000/api/annotate',
    json={
        'source': 'upload',
        'filename': upload_data['filename']
    }
)
job_data = response.json()
job_id = job_data['job_id']

# Polling
import time
while True:
    response = requests.get(f'http://localhost:5000/api/jobs/{job_id}/status')
    status = response.json()
    
    if status['status'] in ['completed', 'error']:
        break
    
    time.sleep(3)

# Download
response = requests.get(f'http://localhost:5000/api/jobs/{job_id}/files/json')
with open('result.json', 'wb') as f:
    f.write(response.content)
```

### JavaScript

```javascript
// Upload
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const upload = await fetch('/api/upload', {
  method: 'POST',
  body: formData
});
const uploadData = await upload.json();

// Anotar
const annotate = await fetch('/api/annotate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    source: 'upload',
    filename: uploadData.filename
  })
});
const jobData = await annotate.json();

// Polling
const pollStatus = async (jobId) => {
  const response = await fetch(`/api/jobs/${jobId}/status`);
  const status = await response.json();
  
  if (status.status === 'completed') {
    console.log('Concluído!');
  } else if (status.status === 'error') {
    console.error('Erro:', status.message);
  } else {
    setTimeout(() => pollStatus(jobId), 3000);
  }
};

pollStatus(jobData.job_id);
```
