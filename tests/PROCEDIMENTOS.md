# Procedimentos de Testes - Bakta Flow

## Índice

1. [Configuração do Ambiente](#configuração-do-ambiente)
2. [Execução de Testes](#execução-de-testes)
3. [Testes Unitários](#testes-unitários)
4. [Testes de Integração](#testes-de-integração)
5. [Testes End-to-End](#testes-end-to-end)
6. [Testes de Performance](#testes-de-performance)
7. [Relatórios](#relatórios)
8. [CI/CD](#cicd)

---

## Configuração do Ambiente

### 1. Instalação de Dependências

```bash
# Acesse o diretório do projeto
cd Bakta

# Crie um ambiente virtual para testes
conda create -n bakta_test python=3.10 -y
conda activate bakta_test

# Instale as dependências
pip install -r requirements.txt

# Instale as dependências de desenvolvimento/teste
pip install pytest pytest-cov pytest-html pytest-xdist requests
```

### 2. Estrutura de Diretórios de Teste

```
tests/
├── conftest.py              # Configurações e fixtures
├── ESPECIFICACOES.md        # Este documento
├── PROCEDIMENTOS.md         # Procedimentos
├── fixtures/                # Dados de teste
│   ├── sample.fasta
│   └── sample_result.json
├── unit/                    # Testes unitários
│   ├── test_pipeline.py
│   └── test_api.py
├── integration/             # Testes de integração
│   └── test_integration.py
└── e2e/                     # Testes end-to-end
    └── test_e2e.py
```

### 3. Configuração do pytest

Crie o arquivo `pytest.ini` na raiz:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
markers =
    unit: Testes unitários (rápidos)
    integration: Testes de integração
    e2e: Testes end-to-end
    slow: Testes lentos
```

---

## Execução de Testes

### Execução Completa

```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=backend --cov-report=html --cov-report=term

# Com relatório HTML
pytest --html=reports/test_report.html --self-contained-html
```

### Execução por Tipo

```bash
# Apenas testes unitários
pytest -m unit

# Apenas testes de integração
pytest -m integration

# Apenas testes E2E
pytest -m e2e

# Excluir testes lentos
pytest -m "not slow"
```

### Execução por Arquivo

```bash
# Testes do pipeline
pytest tests/unit/test_pipeline.py

# Testes da API
pytest tests/unit/test_api.py

# Testes de integração
pytest tests/integration/test_integration.py
```

### Execução de Teste Específico

```bash
# Por nome
pytest -k "test_pipeline_creation"

# Por classe
pytest tests/unit/test_pipeline.py::TestPipelineInitialization

# Por método específico
pytest tests/unit/test_pipeline.py::TestPipelineInitialization::test_pipeline_creation_default
```

### Modo Debug

```bash
# Com PDB
pytest --pdb

# Parar no primeiro erro
pytest -x

# Detalhes completos
pytest -vvv

# Mostrar saída de print
pytest -s
```

---

## Testes Unitários

### Preparação

```bash
# Ativar ambiente
conda activate bakta_test

# Verificar instalação
pytest --version
```

### Execução

```bash
# Todos os testes unitários
pytest tests/unit -v

# Com cobertura detalhada
pytest tests/unit --cov=backend/pipeline --cov-report=term-missing

# Paralelo (mais rápido)
pytest tests/unit -n auto
```

### Verificação de Cobertura

```bash
# Gerar relatório de cobertura
pytest tests/unit --cov=backend --cov-report=html

# Abrir relatório
open htmlcov/index.html  # Linux/Mac
start htmlcov/index.html  # Windows
```

### Critérios de Aprovação

| Métrica | Mínimo | Ideal |
|---------|--------|-------|
| Cobertura de linhas | 80% | 90% |
| Cobertura de funções | 90% | 100% |
| Testes passando | 100% | 100% |
| Tempo de execução | < 30s | < 10s |

---

## Testes de Integração

### Preparação

```bash
# Verificar se backend está configurado
export PYTHONPATH=./backend:$PYTHONPATH

# Verificar diretórios
mkdir -p resultados data/uploads data/templates
```

### Execução

```bash
# Todos os testes de integração
pytest tests/integration -v -m integration

# Com setup completo
pytest tests/integration/test_integration.py::TestFullWorkflow -v
```

### Testes Manuais de API

```bash
# Usando curl

# 1. Verificar status
curl http://localhost:5000/api/status

# 2. Upload
curl -X POST -F "file=@tests/fixtures/sample.fasta" \
  http://localhost:5000/api/upload

# 3. Anotação
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"source":"upload","filename":"..."}' \
  http://localhost:5000/api/annotate

# 4. Listar jobs
curl http://localhost:5000/api/jobs
```

### Postman / Insomnia

Importe a coleção:

```json
{
  "info": {
    "name": "Bakta Flow API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/"
  },
  "item": [
    {
      "name": "Status",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/api/status"
      }
    },
    {
      "name": "Upload",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/api/upload",
        "body": {
          "mode": "formdata",
          "formdata": [
            {"key": "file", "type": "file", "src": "sample.fasta"}
          ]
        }
      }
    }
  ],
  "variable": [
    {"key": "base_url", "value": "http://localhost:5000"}
  ]
}
```

---

## Testes End-to-End

### Preparação

```bash
# Iniciar aplicação
conda activate bakta_env
python backend/app.py &

# Ou com Docker
cd deployment && docker-compose up -d

# Aguardar inicialização
sleep 5
```

### Execução

```bash
# Todos os testes E2E
pytest tests/e2e -v -m e2e

# Fluxo completo
pytest tests/e2e/test_e2e.py::TestEndToEndWorkflow::test_complete_user_workflow -v

# Cenários específicos
pytest tests/e2e/test_e2e.py::TestEndToEndWorkflow::test_template_based_annotation -v
```

### Testes Manuais E2E

**Checklist de Testes Manuais:**

```markdown
## Cenário 1: Primeiro Acesso
- [ ] Acessar http://localhost:5000
- [ ] Verificar carregamento da página (< 3s)
- [ ] Verificar todos os templates listados
- [ ] Verificar estatísticas em zero

## Cenário 2: Upload e Anotação
- [ ] Arrastar arquivo FASTA para área de upload
- [ ] Verificar preview do arquivo
- [ ] Clicar "Iniciar Anotação"
- [ ] Verificar barra de progresso
- [ ] Aguardar conclusão
- [ ] Verificar job na lista

## Cenário 3: Download de Resultados
- [ ] Clicar em job concluído
- [ ] Clicar em "Download"
- [ ] Verificar arquivo baixado
- [ ] Verificar conteúdo do arquivo

## Cenário 4: Remoção
- [ ] Clicar em ícone de lixeira
- [ ] Confirmar remoção
- [ ] Verificar que job sumiu da lista
```

---

## Testes de Performance

### Preparação

```bash
# Instalar ferramentas
pip install locust
```

### Teste de Carga com Locust

Crie `locustfile.py`:

```python
from locust import HttpUser, task, between

class BaktaUser(HttpUser):
    wait_time = between(1, 5)
    
    @task(1)
    def status(self):
        self.client.get("/api/status")
    
    @task(2)
    def list_templates(self):
        self.client.get("/api/templates")
    
    @task(3)
    def list_jobs(self):
        self.client.get("/api/jobs")
```

Execução:

```bash
# Iniciar Locust
locust -f locustfile.py --host=http://localhost:5000

# Acessar interface: http://localhost:8089
# Configurar: 50 usuários, taxa de spawn 10
```

### Teste de Carga com pytest

```bash
# Testes de performance
pytest tests/e2e/test_e2e.py::TestLoad -v -m "e2e and slow"
```

### Métricas de Performance

| Métrica | Ferramenta | Limite |
|---------|------------|--------|
| Tempo de resposta | Locust | p95 < 200ms |
| Throughput | Locust | > 100 req/s |
| Tempo de anotação | Timer | < 2x CLI |
| Uso de memória | psutil | < 4GB |
| Uso de CPU | psutil | < 80% |

---

## Relatórios

### Geração de Relatórios

```bash
# Relatório completo com cobertura
pytest \
  --html=reports/test_report.html \
  --cov=backend \
  --cov-report=html:reports/coverage \
  --cov-report=xml:reports/coverage.xml \
  --junitxml=reports/junit.xml
```

### Estrutura do Relatório

```
reports/
├── test_report.html      # Relatório HTML de testes
├── coverage/             # Relatório de cobertura
│   └── index.html
├── coverage.xml          # Cobertura em XML
└── junit.xml             # Resultados JUnit
```

### Interpretação de Resultados

**Relatório pytest-html:**

```
============================= test session starts =============================
platform linux -- Python 3.10.0
pytest-html 4.0.0

Results (12.34s):
   45 passed
    2 failed
    1 xfailed
    5 skipped
```

**Relatório de Cobertura:**

```
Name                      Stmts   Miss  Cover   Missing
-------------------------------------------------------
backend/pipeline.py         200     20    90%   45-50, 120-130
backend/app.py              150     15    90%   80-85, 200-210
-------------------------------------------------------
TOTAL                       350     35    90%
```

---

## CI/CD

### GitHub Actions

Crie `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install pytest pytest-cov
        pip install -r requirements.txt
    
    - name: Run unit tests
      run: pytest tests/unit -v --cov=backend --cov-report=xml
    
    - name: Run integration tests
      run: pytest tests/integration -v
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest tests/unit -q
        language: system
        types: [python]
        pass_filenames: false
        always_run: true
```

---

## Troubleshooting

### Problemas Comuns

**1. ImportError: No module named 'backend'**

```bash
# Solução
export PYTHONPATH=./backend:$PYTHONPATH
# Ou
conda develop ./backend
```

**2. PermissionError ao criar diretórios**

```bash
# Solução
chmod 755 resultados/ data/
```

**3. Tests failing com "Address already in use"**

```bash
# Solução
lsof -i :5000
kill -9 <PID>
```

**4. Coverage não inclui todos os arquivos**

```bash
# Solução
pytest --cov=backend --cov-config=.coveragerc
```

### Debug de Testes

```bash
# Executar com debug
pytest tests/unit/test_pipeline.py -v --pdb

# No PDB:
# (Pdb) pp result  # Pretty print
# (Pdb) pipeline   # Inspecionar objeto
# (Pdb) c          # Continue
```

---

## Checklist de Qualidade

Antes de cada release:

- [ ] Todos os testes unitários passando
- [ ] Cobertura de código >= 80%
- [ ] Testes de integração passando
- [ ] Testes E2E passando
- [ ] Testes de performance dentro dos limites
- [ ] Documentação atualizada
- [ ] CHANGELOG.md atualizado
- [ ] Sem warnings de depreciação

---

## Contato

Em caso de dúvidas sobre testes:

- **Responsável:** Equipe de QA PUC Minas
- **Email:** qa@pucminas.br
- **Slack:** #projeto-bakta
