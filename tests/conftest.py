#!/usr/bin/env python3
"""
Bakta Flow Test Configuration
Configuração e fixtures para pytest
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

import pytest

# Adicionar backend ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from pipeline import BaktaPipeline


# ============== FIXTURES ==============

@pytest.fixture
def temp_dir():
    """Cria um diretório temporário para testes."""
    temp_path = Path(tempfile.mkdtemp(prefix="bakta_test_"))
    yield temp_path
    # Cleanup
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_fasta(temp_dir):
    """Cria um arquivo FASTA de exemplo para testes."""
    fasta_path = temp_dir / "sample.fasta"
    fasta_content = """>sample_genome_1
ATGAAACGCATTAGCACCACCATTACCACCACCATCACCATTACCACAGGTAACGGTGCGGGCTGA
ATGAAACGCATTAGCACCACCATTACCACCACCATCACCATTACCACAGGTAACGGTGCGGGCTGA
ATGAAACGCATTAGCACCACCATTACCACCACCATCACCATTACCACAGGTAACGGTGCGGGCTGA
>sample_genome_2
GCTGAATGAAACGCATTAGCACCACCATTACCACCACCATCACCATTACCACAGGTAACGGTGCGG
GCTGAATGAAACGCATTAGCACCACCATTACCACCACCATCACCATTACCACAGGTAACGGTGCGG
"""
    fasta_path.write_text(fasta_content)
    return fasta_path


@pytest.fixture
def sample_fasta_invalid(temp_dir):
    """Cria um arquivo FASTA inválido para testes."""
    invalid_path = temp_dir / "invalid.txt"
    invalid_path.write_text("Este não é um arquivo FASTA válido\nSem cabeçalho\nATCG")
    return invalid_path


@pytest.fixture
def mock_db_path(temp_dir):
    """Cria uma estrutura mock do database Bakta."""
    db_path = temp_dir / "bakta-mock"
    db_path.mkdir()
    
    # Criar arquivos esperados pelo Bakta
    (db_path / "bakta.db").touch()
    (db_path / "version.json").write_text(json.dumps({"version": "1.0"}))
    
    return db_path


@pytest.fixture
def pipeline(temp_dir, mock_db_path):
    """Cria uma instância do pipeline para testes."""
    output_dir = temp_dir / "results"
    return BaktaPipeline(
        db_path=str(mock_db_path),
        output_dir=str(output_dir),
        threads=1,
        meta_mode=True
    )


@pytest.fixture
def sample_job_result(temp_dir):
    """Cria um resultado de job de exemplo."""
    job_dir = temp_dir / "20260314_120000_test_job"
    job_dir.mkdir()
    
    result = {
        "job_id": "20260314_120000_test_job",
        "status": "completed",
        "prefix": "test_genome",
        "output_dir": str(job_dir),
        "files": {
            "json": {
                "path": str(job_dir / "test_genome.json"),
                "description": "Resultados JSON",
                "size": 1500
            },
            "gff3": {
                "path": str(job_dir / "test_genome.gff3"),
                "description": "Anotação GFF3",
                "size": 8500
            }
        },
        "stats": {
            "genome_size": 50000,
            "gc_content": 52.5,
            "n_contigs": 2,
            "cds": 45,
            "genes": 45,
            "trnas": 3,
            "rrnas": 2
        }
    }
    
    # Salvar job_summary.json
    summary_file = job_dir / "job_summary.json"
    summary_file.write_text(json.dumps(result, indent=2))
    
    # Criar arquivos de saída mock
    (job_dir / "test_genome.json").write_text(json.dumps({"version": "1.0"}))
    (job_dir / "test_genome.gff3").write_text("##gff-version 3\n")
    
    return result


@pytest.fixture
def client(temp_dir):
    """Cria um cliente de teste Flask."""
    import sys
    backend_path = Path(__file__).parent.parent / "backend"
    sys.path.insert(0, str(backend_path))
    
    from app import app
    
    app.config['TESTING'] = True
    app.config['UPLOAD_FOLDER'] = str(temp_dir / "uploads")
    
    with app.test_client() as client:
        yield client


# ============== HELPERS ==============

def create_mock_fasta(path: Path, num_sequences: int = 1, seq_length: int = 1000):
    """Helper para criar arquivos FASTA mock."""
    import random
    bases = ['A', 'T', 'G', 'C']
    
    lines = []
    for i in range(num_sequences):
        lines.append(f">sequence_{i+1}")
        seq = ''.join(random.choices(bases, k=seq_length))
        # Quebrar em linhas de 60 caracteres
        for j in range(0, len(seq), 60):
            lines.append(seq[j:j+60])
    
    path.write_text('\n'.join(lines))
    return path


def assert_fasta_format(content: str):
    """Verifica se o conteúdo é um formato FASTA válido."""
    lines = content.strip().split('\n')
    assert lines[0].startswith('>'), "FASTA deve começar com >"
    
    valid_bases = set('ATCGNatcgn\n')
    for line in lines[1:]:
        if not line.startswith('>'):
            assert set(line).issubset(valid_bases), f"Sequência inválida: {line[:20]}"


# ============== CONFIGURAÇÃO PYTEST ==============

def pytest_configure(config):
    """Configuração global do pytest."""
    config.addinivalue_line(
        "markers", "slow: marca testes que são lentos (requerem Bakta real)"
    )
    config.addinivalue_line(
        "markers", "integration: marca testes de integração"
    )
    config.addinivalue_line(
        "markers", "unit: marca testes unitários"
    )


def pytest_collection_modifyitems(config, items):
    """Modifica itens de teste durante a coleta."""
    # Adicionar marker 'unit' para testes que não têm marker específico
    for item in items:
        if not any(marker.name in ['unit', 'integration', 'e2e', 'slow'] 
                   for marker in item.iter_markers()):
            item.add_marker(pytest.mark.unit)
