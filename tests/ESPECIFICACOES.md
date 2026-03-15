# Especificações de Testes - Bakta Flow

## Índice

1. [Visão Geral](#visão-geral)
2. [Tipos de Testes](#tipos-de-testes)
3. [Especificações por Módulo](#especificações-por-módulo)
4. [Casos de Teste](#casos-de-teste)
5. [Critérios de Aceitação](#critérios-de-aceitação)

---

## Visão Geral

### Objetivo

Definir especificações completas de testes para garantir qualidade, confiabilidade e performance do sistema Bakta Flow.

### Escopo

| Componente | Cobertura |
|------------|-----------|
| Backend API | 100% endpoints |
| Pipeline | 100% funções principais |
| Frontend | Fluxos críticos |
| Integração | Sistema completo |
| Performance | Carga e stress |

---

## Tipos de Testes

### 1. Testes Unitários (`tests/unit/`)

**Objetivo:** Testar unidades isoladas de código

**Cobertura:**
- Funções individuais
- Classes e métodos
- Validações
- Tratamento de erros

**Exemplo:**
```python
def test_pipeline_creation():
    """Testa criação do pipeline com parâmetros válidos."""
    pipeline = BaktaPipeline(
        db_path="./db",
        output_dir="./out",
        threads=4
    )
    assert pipeline.threads == 4
```

### 2. Testes de Integração (`tests/integration/`)

**Objetivo:** Testar interação entre componentes

**Cobertura:**
- API + Pipeline
- Upload + Processamento
- Banco de dados (filesystem)
- Jobs concorrentes

**Exemplo:**
```python
def test_upload_and_annotate():
    """Testa fluxo completo de upload até anotação."""
    # 1. Upload arquivo
    # 2. Iniciar anotação
    # 3. Verificar job criado
```

### 3. Testes End-to-End (`tests/e2e/`)

**Objetivo:** Testar fluxo completo do usuário

**Cobertura:**
- Cenários reais de uso
- Múltiplas operações sequenciais
- Recuperação de erros
- Performance sob carga

---

## Especificações por Módulo

### Módulo: Pipeline (`pipeline.py`)

#### Classe: `BaktaPipeline`

| Método | Tipo de Teste | Entrada | Saída Esperada |
|--------|---------------|---------|----------------|
| `__init__` | Unitário | `db_path`, `output_dir`, `threads` | Instância configurada |
| `check_bakta_installation` | Unitário | - | `True` se instalado |
| `check_database` | Unitário | - | `True` se DB existe |
| `run_annotation` | Integração | FASTA válido | Job completado |
| `run_annotation` | Unitário | FASTA inválido | Erro apropriado |
| `list_jobs` | Unitário | - | Lista de jobs |
| `get_job` | Unitário | `job_id` | Job ou `None` |
| `delete_job` | Unitário | `job_id` | `True`/`False` |
| `_parse_results` | Unitário | Diretório com resultados | Dict estruturado |

#### Casos de Teste - Pipeline

**TC-P001: Inicialização com parâmetros padrão**
```
Entrada: BaktaPipeline()
Esperado: 
  - db_path = Path("./bakta-light")
  - output_dir = Path("./resultados")
  - threads = 4
  - meta_mode = True
```

**TC-P002: Inicialização com parâmetros customizados**
```
Entrada: BaktaPipeline(
    db_path="/custom/db",
    output_dir="/custom/out",
    threads=8,
    meta_mode=False
)
Esperado:
  - threads = 8
  - meta_mode = False
```

**TC-P003: Criação automática de diretório de saída**
```
Pré-condição: Diretório não existe
Entrada: BaktaPipeline(output_dir="./novo_dir")
Esperado: Diretório criado automaticamente
```

**TC-P004: Verificação de database existente**
```
Pré-condição: Database existe
Entrada: check_database()
Esperado: True
```

**TC-P005: Verificação de database inexistente**
```
Pré-condição: Database não existe
Entrada: check_database()
Esperado: False
```

**TC-P006: Execução com arquivo FASTA válido**
```
Entrada: run_annotation("genome.fasta")
Mock: Bakta retorna sucesso
Esperado: (True, {job_id, status, stats})
```

**TC-P007: Execução com arquivo inexistente**
```
Entrada: run_annotation("/invalid/path.fasta")
Esperado: (False, {error: "Arquivo não encontrado"})
```

**TC-P008: Execução sem Bakta instalado**
```
Mock: Bakta não instalado
Entrada: run_annotation("genome.fasta")
Esperado: (False, {error: "Bakta não instalado"})
```

**TC-P009: Parse de resultados JSON**
```
Entrada: Diretório com {prefix}.json válido
Esperado: Dict com stats, files, job_id
```

**TC-P010: Listagem de jobs**
```
Pré-condição: 3 jobs existem
Entrada: list_jobs()
Esperado: Lista com 3 elementos, ordenados por data
```

**TC-P011: Remoção de job existente**
```
Entrada: delete_job("job_existente")
Esperado: True, diretório removido
```

**TC-P012: Remoção de job inexistente**
```
Entrada: delete_job("job_inexistente")
Esperado: False
```

---

### Módulo: API Flask (`app.py`)

#### Endpoints

| Endpoint | Método | Tipo | Casos de Teste |
|----------|--------|------|----------------|
| `/` | GET | E2E | Renderização, conteúdo |
| `/api/status` | GET | Unitário | Resposta 200, campos obrigatórios |
| `/api/templates` | GET | Unitário/Integração | Lista vazia, com templates |
| `/api/upload` | POST | Unitário/Integração | Arquivo válido, inválido, grande |
| `/api/annotate` | POST | Integração | Upload/template, sucesso/erro |
| `/api/jobs` | GET | Unitário/Integração | Lista, ordenação |
| `/api/jobs/<id>` | GET | Unitário | Existe, não existe |
| `/api/jobs/<id>/status` | GET | Integração | Em memória, em disco |
| `/api/jobs/<id>` | DELETE | Unitário | Sucesso, não existe |
| `/api/jobs/<id>/files/<type>` | GET | Unitário | Download existe/não existe |
| `/api/stats` | GET | Integração | Estatísticas corretas |
| `/api/bakta/check` | GET | Unitário | Instalado/não instalado |

#### Casos de Teste - API

**TC-A001: Status da API**
```
GET /api/status
Esperado:
  Status: 200
  Body: {status: "ok", service, version, timestamp}
```

**TC-A002: Upload de arquivo FASTA válido**
```
POST /api/upload
Body: multipart/form-data com arquivo .fasta
Esperado:
  Status: 200
  Body: {success: true, filename, size}
  Arquivo salvo no diretório de uploads
```

**TC-A003: Upload de arquivo sem extensão permitida**
```
POST /api/upload
Body: arquivo .txt
Esperado:
  Status: 400
  Body: {error: "Tipo de arquivo não permitido"}
```

**TC-A004: Upload sem arquivo**
```
POST /api/upload
Body: vazio
Esperado:
  Status: 400
  Body: {error: "Nenhum arquivo enviado"}
```

**TC-A005: Upload de arquivo grande (>100MB)**
```
POST /api/upload
Body: arquivo ~101MB
Esperado:
  Status: 413
  Body: {error: "Arquivo muito grande"}
```

**TC-A006: Início de anotação com upload**
```
Pré-condição: Arquivo uploadado
POST /api/annotate
Body: {source: "upload", filename: "..."}
Esperado:
  Status: 200
  Body: {success: true, job_id, status: "started"}
  Thread iniciada
```

**TC-A007: Início de anotação com template**
```
POST /api/annotate
Body: {source: "template", filename: "ecoli.fasta"}
Esperado:
  Status: 200
  Body: {success: true, job_id}
```

**TC-A008: Anotação de arquivo inexistente**
```
POST /api/annotate
Body: {source: "upload", filename: "nao_existe.fasta"}
Esperado:
  Status: 404
  Body: {error: "Arquivo não encontrado"}
```

**TC-A009: Anotação sem dados**
```
POST /api/annotate
Body: vazio
Esperado:
  Status: 400
  Body: {error: "Dados não fornecidos"}
```

**TC-A010: Listagem de jobs**
```
GET /api/jobs
Esperado:
  Status: 200
  Body: {jobs: [...], total: N}
  Jobs ordenados por data (mais recente primeiro)
```

**TC-A011: Obtenção de job existente**
```
GET /api/jobs/{job_id}
Esperado:
  Status: 200
  Body: {job_id, status, stats, files}
```

**TC-A012: Obtenção de job inexistente**
```
GET /api/jobs/nao_existe
Esperado:
  Status: 404
  Body: {error: "Job não encontrado"}
```

**TC-A013: Status de job em execução**
```
GET /api/jobs/{job_id}/status
Pré-condição: Job em memória
Esperado:
  Status: 200
  Body: {status: "running", progress, message}
```

**TC-A014: Download de arquivo de resultado**
```
GET /api/jobs/{job_id}/files/json
Esperado:
  Status: 200
  Content-Type: application/octet-stream
  Content-Disposition: attachment
```

**TC-A015: Remoção de job**
```
DELETE /api/jobs/{job_id}
Esperado:
  Status: 200
  Body: {success: true}
  Diretório removido
```

**TC-A016: Estatísticas gerais**
```
GET /api/stats
Esperado:
  Status: 200
  Body: {total_jobs, completed, errors, total_cds_annotated}
```

---

### Módulo: Frontend (`frontend/`)

#### Componentes

| Componente | Tipo de Teste | Eventos |
|------------|---------------|---------|
| Upload Area | E2E | Drag & drop, click, seleção |
| Template Cards | E2E | Click, seleção visual |
| Progress Bar | E2E/Visual | Atualização, animação |
| Job List | E2E | Renderização, interação |
| Download Buttons | E2E | Click, download |

#### Casos de Teste - Frontend

**TC-F001: Upload via drag & drop**
```
Ação: Arrastar arquivo FASTA para área de upload
Esperado:
  - Visualização de hover
  - Arquivo aceito
  - Nome exibido
  - Botão "Iniciar" habilitado
```

**TC-F002: Upload via click**
```
Ação: Clicar na área de upload, selecionar arquivo
Esperado: Mesmo que TC-F001
```

**TC-F003: Seleção de template**
```
Ação: Clicar em card de template
Esperado:
  - Card destacado (classe 'selected')
  - Upload area escondida
  - Botão "Iniciar" habilitado
```

**TC-F004: Progresso em tempo real**
```
Pré-condição: Anotação iniciada
Esperado:
  - Barra de progresso visível
  - Porcentagem atualizada
  - Mensagem de status
  - Spinner animado
```

**TC-F005: Lista de jobs**
```
Ação: Acessar página
Esperado:
  - Jobs ordenados por data
  - Badges de status (corretos)
  - Contadores de features
  - Botões de ação
```

**TC-F006: Download de resultado**
```
Ação: Click em botão download
Esperado:
  - Arquivo baixado
  - Nome correto
  - Conteúdo válido
```

**TC-F007: Responsividade**
```
Testar em: Desktop, Tablet, Mobile
Esperado:
  - Layout adaptativo
  - Elementos visíveis
  - Scroll funcional
```

---

## Casos de Teste

### Cenário: Usuário Real

**CT-U001: Primeira anotação**
```
Perfil: Usuário novo
Fluxo:
  1. Acessar aplicação
  2. Selecionar template "E. coli"
  3. Clicar "Iniciar Anotação"
  4. Aguardar conclusão
  5. Verificar resultados
  6. Download GFF3
Critérios:
  - Tempo total < 10 minutos
  - Nenhum erro
  - Resultados completos
```

**CT-U002: Upload de genoma próprio**
```
Perfil: Pesquisador
Fluxo:
  1. Acessar aplicação
  2. Arrastar arquivo FASTA (~2MB)
  3. Definir prefixo
  4. Iniciar anotação
  5. Monitorar progresso
  6. Download todos os formatos
Critérios:
  - Upload < 30 segundos
  - Progresso atualizado a cada 3s
  - Todos os arquivos gerados
```

**CT-U003: Múltiplas anotações**
```
Perfil: Usuário avançado
Fluxo:
  1. Iniciar 5 anotações em sequência
  2. Verificar lista de jobs
  3. Remover job antigo
Critérios:
  - Jobs executam sem interferência
  - Lista atualizada corretamente
  - Remoção limpa todos os arquivos
```

---

## Critérios de Aceitação

### Funcionais

| ID | Critério | Prioridade |
|----|----------|------------|
| CA-F01 | Upload de FASTA até 100MB | Alta |
| CA-F02 | Suporte a templates NCBI | Alta |
| CA-F03 | Geração de todos os formatos de saída | Alta |
| CA-F04 | Listagem e gestão de jobs | Alta |
| CA-F05 | Download individual de arquivos | Alta |
| CA-F06 | Feedback visual de progresso | Média |
| CA-F07 | Validação de inputs | Alta |

### Não-Funcionais

| ID | Critério | Métrica |
|----|----------|---------|
| CA-NF01 | Tempo de resposta API | < 100ms (p95) |
| CA-NF02 | Throughput de upload | > 5MB/s |
| CA-NF03 | Tempo de anotação | < 2x tempo Bakta CLI |
| CA-NF04 | Disponibilidade | > 99% |
| CA-NF05 | Cobertura de testes | > 80% |
| CA-NF06 | Concurrent users | > 10 simultâneos |

### Compatibilidade

| Navegador | Versão Mínima |
|-----------|---------------|
| Chrome | 90+ |
| Firefox | 88+ |
| Safari | 14+ |
| Edge | 90+ |

---

## Matriz de Rastreabilidade

| Requisito | Testes Relacionados |
|-----------|---------------------|
| Upload de arquivos | TC-A002, TC-A003, TC-A004, TC-A005 |
| Anotação genômica | TC-A006, TC-A007, TC-P006, TC-P007 |
| Gestão de jobs | TC-A010, TC-A011, TC-A013, TC-A015 |
| Download de resultados | TC-A014 |
| Validação de inputs | TC-A003, TC-A004, TC-A008 |
| Interface web | TC-F001, TC-F002, TC-F003 |

---

## Registro de Alterações

| Versão | Data | Alterações |
|--------|------|------------|
| 1.0 | 2026-03-15 | Documento inicial |
