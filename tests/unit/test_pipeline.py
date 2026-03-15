#!/usr/bin/env python3
"""
Bakta Flow Pipeline Unit Tests
Testes unitários para o módulo pipeline.py
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from pipeline import BaktaPipeline


# ============== TESTES DE INICIALIZAÇÃO ==============

class TestPipelineInitialization:
    """Testes para inicialização do pipeline."""
    
    def test_pipeline_creation_default(self, temp_dir):
        """Testa criação do pipeline com parâmetros padrão."""
        pipeline = BaktaPipeline()
        
        assert pipeline.db_path.name == "bakta-light"
        assert pipeline.output_dir.name == "resultados"
        assert pipeline.threads == 4
        assert pipeline.meta_mode is True
    
    def test_pipeline_creation_custom(self, temp_dir, mock_db_path):
        """Testa criação do pipeline com parâmetros customizados."""
        output_dir = temp_dir / "custom_results"
        
        pipeline = BaktaPipeline(
            db_path=str(mock_db_path),
            output_dir=str(output_dir),
            threads=8,
            meta_mode=False
        )
        
        assert pipeline.db_path == mock_db_path
        assert pipeline.output_dir == output_dir
        assert pipeline.threads == 8
        assert pipeline.meta_mode is False
    
    def test_output_dir_created(self, temp_dir, mock_db_path):
        """Testa se diretório de saída é criado automaticamente."""
        output_dir = temp_dir / "new_results"
        
        assert not output_dir.exists()
        
        pipeline = BaktaPipeline(
            db_path=str(mock_db_path),
            output_dir=str(output_dir)
        )
        
        assert output_dir.exists()
        assert output_dir.is_dir()


# ============== TESTES DE VALIDAÇÃO ==============

class TestPipelineValidation:
    """Testes para validação de inputs."""
    
    def test_check_database_exists(self, temp_dir, mock_db_path):
        """Testa verificação quando database existe."""
        pipeline = BaktaPipeline(db_path=str(mock_db_path))
        
        # Mock para simular database existente
        assert pipeline.check_database() is True
    
    def test_check_database_not_exists(self, temp_dir):
        """Testa verificação quando database não existe."""
        nonexistent_db = temp_dir / "nonexistent"
        pipeline = BaktaPipeline(db_path=str(nonexistent_db))
        
        assert pipeline.check_database() is False
    
    @patch('pipeline.subprocess.run')
    def test_check_bakta_installed(self, mock_run, temp_dir, mock_db_path):
        """Testa verificação quando Bakta está instalado."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="bakta 1.9.4\n"
        )
        
        pipeline = BaktaPipeline(db_path=str(mock_db_path))
        
        assert pipeline.check_bakta_installation() is True
        mock_run.assert_called_once()
    
    @patch('pipeline.subprocess.run')
    def test_check_bakta_not_installed(self, mock_run, temp_dir, mock_db_path):
        """Testa verificação quando Bakta não está instalado."""
        mock_run.side_effect = FileNotFoundError()
        
        pipeline = BaktaPipeline(db_path=str(mock_db_path))
        
        assert pipeline.check_bakta_installation() is False


# ============== TESTES DE GESTÃO DE JOBS ==============

class TestJobManagement:
    """Testes para gestão de jobs."""
    
    def test_create_job_dir(self, pipeline):
        """Testa criação de diretório para job."""
        job_id = "test_job_001"
        job_dir = pipeline.create_job_dir(job_id)
        
        assert job_dir.exists()
        assert job_dir.is_dir()
        assert job_dir.name == job_id
        assert job_dir.parent == pipeline.output_dir
    
    def test_list_jobs_empty(self, pipeline):
        """Testa listagem quando não há jobs."""
        jobs = pipeline.list_jobs()
        
        assert isinstance(jobs, list)
        assert len(jobs) == 0
    
    def test_list_jobs_with_results(self, pipeline, sample_job_result):
        """Testa listagem com jobs existentes."""
        jobs = pipeline.list_jobs()
        
        assert len(jobs) == 1
        assert jobs[0]['job_id'] == sample_job_result['job_id']
        assert jobs[0]['status'] == 'completed'
    
    def test_get_job_exists(self, pipeline, sample_job_result):
        """Testa obtenção de job existente."""
        job = pipeline.get_job(sample_job_result['job_id'])
        
        assert job is not None
        assert job['job_id'] == sample_job_result['job_id']
        assert 'stats' in job
    
    def test_get_job_not_exists(self, pipeline):
        """Testa obtenção de job inexistente."""
        job = pipeline.get_job("nonexistent_job")
        
        assert job is None
    
    def test_delete_job_success(self, pipeline, sample_job_result):
        """Testa remoção bem-sucedida de job."""
        job_id = sample_job_result['job_id']
        
        assert pipeline.delete_job(job_id) is True
        assert pipeline.get_job(job_id) is None
    
    def test_delete_job_not_exists(self, pipeline):
        """Testa remoção de job inexistente."""
        assert pipeline.delete_job("nonexistent") is False


# ============== TESTES DE PARSE DE RESULTADOS ==============

class TestResultParsing:
    """Testes para parse de resultados."""
    
    def test_parse_results_json(self, pipeline, sample_job_result):
        """Testa parse de resultados JSON."""
        job_dir = Path(sample_job_result['output_dir'])
        prefix = sample_job_result['prefix']
        job_id = sample_job_result['job_id']
        
        result = pipeline._parse_results(job_dir, prefix, job_id)
        
        assert result['job_id'] == job_id
        assert result['status'] == 'completed'
        assert 'files' in result
        assert 'stats' in result
        assert result['stats']['cds'] == 45
    
    def test_parse_results_missing_json(self, pipeline, temp_dir):
        """Testa parse quando JSON está ausente."""
        job_dir = temp_dir / "test_job"
        job_dir.mkdir()
        
        # Criar apenas arquivos não-JSON
        (job_dir / "test.txt").write_text("summary")
        
        result = pipeline._parse_results(job_dir, "test", "test_job")
        
        assert result['stats'] == {}  # Stats vazio quando não há JSON


# ============== TESTES DE EXECUÇÃO (MOCK) ==============

class TestPipelineExecution:
    """Testes para execução do pipeline (com mocks)."""
    
    @patch('pipeline.subprocess.Popen')
    def test_run_annotation_success(self, mock_popen, pipeline, sample_fasta):
        """Testa execução bem-sucedida da anotação."""
        # Mock do processo
        mock_process = MagicMock()
        mock_process.stdout = iter(["Line 1\n", "Line 2\n"])
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process
        
        # Mock check_bakta_installation
        pipeline.check_bakta_installation = Mock(return_value=True)
        
        success, result = pipeline.run_annotation(
            fasta_path=str(sample_fasta),
            job_id="test_run_001",
            prefix="test",
            verbose=False
        )
        
        assert success is True
        assert result['job_id'] == "test_run_001"
        assert result['status'] == 'completed'
    
    @patch('pipeline.subprocess.Popen')
    def test_run_annotation_failure(self, mock_popen, pipeline, sample_fasta):
        """Testa execução com falha."""
        # Mock do processo com erro
        mock_process = MagicMock()
        mock_process.stdout = iter(["Error line\n"])
        mock_process.wait.return_value = 1
        mock_popen.return_value = mock_process
        
        pipeline.check_bakta_installation = Mock(return_value=True)
        
        success, result = pipeline.run_annotation(
            fasta_path=str(sample_fasta),
            job_id="test_run_fail",
            verbose=False
        )
        
        assert success is False
        assert 'error' in result
    
    def test_run_annotation_fasta_not_found(self, pipeline):
        """Testa execução quando FASTA não existe."""
        success, result = pipeline.run_annotation(
            fasta_path="/nonexistent/file.fasta"
        )
        
        assert success is False
        assert 'error' in result
        assert 'não encontrado' in result['error']
    
    def test_run_annotation_bakta_not_installed(self, pipeline, sample_fasta):
        """Testa execução quando Bakta não está instalado."""
        pipeline.check_bakta_installation = Mock(return_value=False)
        
        success, result = pipeline.run_annotation(
            fasta_path=str(sample_fasta)
        )
        
        assert success is False
        assert 'Bakta não instalado' in result['error']


# ============== TESTES DE ESTATÍSTICAS ==============

class TestStatistics:
    """Testes para cálculo de estatísticas."""
    
    def test_extract_stats_from_bakta_json(self, pipeline, temp_dir):
        """Testa extração de estatísticas de JSON do Bakta."""
        # Criar JSON no formato do Bakta
        bakta_json = {
            "stats": {
                "genome_size": 4639675,
                "gc": 50.79,
                "n_contigs": 1,
                "n50": 4639675,
                "feature_cds": 4243,
                "feature_gene": 4243,
                "feature_trna": 89,
                "feature_rrna": 22
            }
        }
        
        job_dir = temp_dir / "test_stats"
        job_dir.mkdir()
        prefix = "test_genome"
        
        # Salvar JSON
        json_file = job_dir / f"{prefix}.json"
        json_file.write_text(json.dumps(bakta_json))
        
        # Parse
        result = pipeline._parse_results(job_dir, prefix, "test_job")
        
        assert result['stats']['genome_size'] == 4639675
        assert result['stats']['gc_content'] == 50.79
        assert result['stats']['cds'] == 4243
        assert result['stats']['trnas'] == 89
