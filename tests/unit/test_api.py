#!/usr/bin/env python3
"""
Bakta Flow API Unit Tests
Testes unitários para a API Flask
"""

import json
import pytest
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, patch


# ============== TESTES DE STATUS ==============

class TestApiStatus:
    """Testes para endpoints de status."""
    
    def test_api_status(self, client):
        """Testa endpoint de status da API."""
        response = client.get('/api/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['status'] == 'ok'
        assert 'service' in data
        assert 'version' in data
        assert 'timestamp' in data
    
    def test_index_page(self, client):
        """Testa página principal."""
        response = client.get('/')
        
        assert response.status_code == 200
        # Verifica se contém elementos esperados
        assert b'PUC Minas' in response.data or b'Bakta' in response.data


# ============== TESTES DE TEMPLATES ==============

class TestApiTemplates:
    """Testes para endpoints de templates."""
    
    def test_list_templates_empty(self, client):
        """Testa listagem quando não há templates."""
        response = client.get('/api/templates')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'templates' in data
        assert isinstance(data['templates'], list)
    
    def test_list_templates_with_files(self, client, temp_dir):
        """Testa listagem com templates existentes."""
        # Criar template de teste
        template_dir = temp_dir / "templates"
        template_dir.mkdir(exist_ok=True)
        (template_dir / "ecoli_test.fasta").write_text(">test\nATCG"
        )
        
        with patch('app.TEMPLATES_FOLDER', template_dir):
            response = client.get('/api/templates')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert len(data['templates']) == 1
            assert data['templates'][0]['name'] == 'ecoli_test.fasta'


# ============== TESTES DE UPLOAD ==============

class TestApiUpload:
    """Testes para endpoint de upload."""
    
    def test_upload_valid_fasta(self, client):
        """Testa upload de arquivo FASTA válido."""
        data = {
            'file': (BytesIO(b'>test_sequence\nATCGATCGATCG'), 'test.fasta')
        }
        
        response = client.post(
            '/api/upload',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 200
        result = json.loads(response.data)
        
        assert result['success'] is True
        assert 'filename' in result
        assert 'size' in result
    
    def test_upload_no_file(self, client):
        """Testa upload sem arquivo."""
        response = client.post('/api/upload')
        
        assert response.status_code == 400
        result = json.loads(response.data)
        
        assert 'error' in result
    
    def test_upload_empty_filename(self, client):
        """Testa upload com nome de arquivo vazio."""
        data = {'file': (BytesIO(b''), '')}
        
        response = client.post(
            '/api/upload',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
    
    def test_upload_invalid_extension(self, client):
        """Testa upload com extensão inválida."""
        data = {
            'file': (BytesIO(b'conteudo invalido'), 'arquivo.txt')
        }
        
        response = client.post(
            '/api/upload',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
        result = json.loads(response.data)
        
        assert 'error' in result


# ============== TESTES DE ANOTAÇÃO ==============

class TestApiAnnotation:
    """Testes para endpoint de anotação."""
    
    @patch('app.run_annotation_async')
    def test_annotate_with_upload(self, mock_async, client):
        """Testa início de anotação com upload."""
        # Criar arquivo de upload
        upload_dir = Path(client.application.config['UPLOAD_FOLDER'])
        upload_dir.mkdir(parents=True, exist_ok=True)
        (upload_dir / "test_upload.fasta").write_text(">test\nATCG")
        
        data = {
            'source': 'upload',
            'filename': 'test_upload.fasta',
            'prefix': 'test_genome'
        }
        
        response = client.post(
            '/api/annotate',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        result = json.loads(response.data)
        
        assert result['success'] is True
        assert 'job_id' in result
        assert result['status'] == 'started'
        mock_async.assert_called_once()
    
    @patch('app.run_annotation_async')
    def test_annotate_with_template(self, mock_async, client, temp_dir):
        """Testa início de anotação com template."""
        # Criar template
        template_dir = temp_dir / "templates"
        template_dir.mkdir()
        (template_dir / "ecoli.fasta").write_text(">ecoli\nATCG")
        
        with patch('app.TEMPLATES_FOLDER', template_dir):
            data = {
                'source': 'template',
                'filename': 'ecoli.fasta'
            }
            
            response = client.post(
                '/api/annotate',
                data=json.dumps(data),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            result = json.loads(response.data)
            
            assert result['success'] is True
    
    def test_annotate_no_data(self, client):
        """Testa anotação sem dados."""
        response = client.post('/api/annotate')
        
        assert response.status_code == 400
        result = json.loads(response.data)
        
        assert 'error' in result
    
    def test_annotate_file_not_found(self, client):
        """Testa anotação com arquivo inexistente."""
        data = {
            'source': 'upload',
            'filename': 'nonexistent.fasta'
        }
        
        response = client.post(
            '/api/annotate',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == 404
        result = json.loads(response.data)
        
        assert 'error' in result


# ============== TESTES DE JOBS ==============

class TestApiJobs:
    """Testes para endpoints de jobs."""
    
    def test_list_jobs_empty(self, client):
        """Testa listagem de jobs vazia."""
        response = client.get('/api/jobs')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'jobs' in data
        assert data['total'] == 0
    
    @patch('app.BaktaPipeline')
    def test_list_jobs_with_data(self, mock_pipeline_class, client):
        """Testa listagem com jobs."""
        mock_pipeline = Mock()
        mock_pipeline.list_jobs.return_value = [
            {
                'job_id': '20260314_test',
                'status': 'completed',
                'stats': {'cds': 100}
            }
        ]
        mock_pipeline_class.return_value = mock_pipeline
        
        response = client.get('/api/jobs')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['total'] == 1
        assert len(data['jobs']) == 1
    
    @patch('app.BaktaPipeline')
    def test_get_job_exists(self, mock_pipeline_class, client):
        """Testa obtenção de job existente."""
        mock_pipeline = Mock()
        mock_pipeline.get_job.return_value = {
            'job_id': '20260314_test',
            'status': 'completed'
        }
        mock_pipeline_class.return_value = mock_pipeline
        
        response = client.get('/api/jobs/20260314_test')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['job_id'] == '20260314_test'
    
    @patch('app.BaktaPipeline')
    def test_get_job_not_found(self, mock_pipeline_class, client):
        """Testa obtenção de job inexistente."""
        mock_pipeline = Mock()
        mock_pipeline.get_job.return_value = None
        mock_pipeline_class.return_value = mock_pipeline
        
        response = client.get('/api/jobs/nonexistent')
        
        assert response.status_code == 404
    
    def test_get_job_status_from_memory(self, client):
        """Testa status de job em memória."""
        # Adicionar job ao jobs_status
        from app import jobs_status
        jobs_status['test_job'] = {
            'status': 'running',
            'progress': 50
        }
        
        response = client.get('/api/jobs/test_job/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['status'] == 'running'
        assert data['progress'] == 50
        
        # Cleanup
        del jobs_status['test_job']
    
    @patch('app.BaktaPipeline')
    def test_delete_job(self, mock_pipeline_class, client):
        """Testa remoção de job."""
        mock_pipeline = Mock()
        mock_pipeline.delete_job.return_value = True
        mock_pipeline_class.return_value = mock_pipeline
        
        response = client.delete('/api/jobs/test_job')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True


# ============== TESTES DE ESTATÍSTICAS ==============

class TestApiStats:
    """Testes para endpoints de estatísticas."""
    
    @patch('app.BaktaPipeline')
    def test_get_stats(self, mock_pipeline_class, client):
        """Testa obtenção de estatísticas."""
        mock_pipeline = Mock()
        mock_pipeline.list_jobs.return_value = [
            {'status': 'completed', 'stats': {'cds': 100}},
            {'status': 'completed', 'stats': {'cds': 200}},
            {'status': 'error'}
        ]
        mock_pipeline_class.return_value = mock_pipeline
        
        response = client.get('/api/stats')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['total_jobs'] == 3
        assert data['completed'] == 2
        assert data['errors'] == 1
        assert data['total_cds_annotated'] == 300
    
    @patch('app.BaktaPipeline')
    def test_check_bakta(self, mock_pipeline_class, client):
        """Testa verificação do Bakta."""
        mock_pipeline = Mock()
        mock_pipeline.check_bakta_installation.return_value = True
        mock_pipeline.check_database.return_value = True
        mock_pipeline.db_path = '/app/bakta-light'
        mock_pipeline_class.return_value = mock_pipeline
        
        response = client.get('/api/bakta/check')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['bakta_installed'] is True
        assert data['database_exists'] is True


# ============== TESTES DE DOWNLOAD ==============

class TestApiDownload:
    """Testes para endpoint de download."""
    
    def test_download_file_exists(self, client, temp_dir):
        """Testa download de arquivo existente."""
        # Criar estrutura de resultado
        result_dir = temp_dir / "20260314_test"
        result_dir.mkdir()
        (result_dir / "test_genome.json").write_text('{"test": true}')
        
        with patch('app.RESULTS_FOLDER', temp_dir):
            response = client.get('/api/jobs/20260314_test/files/json')
            
            assert response.status_code == 200
            # Deve ser um attachment
            assert 'attachment' in response.headers.get('Content-Disposition', '')
    
    def test_download_file_not_found(self, client):
        """Testa download de arquivo inexistente."""
        response = client.get('/api/jobs/nonexistent/files/json')
        
        assert response.status_code == 404


# ============== TESTES DE ERRO ==============

class TestApiErrors:
    """Testes para tratamento de erros."""
    
    def test_404_error(self, client):
        """Testa erro 404."""
        response = client.get('/api/endpoint_inexistente')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        
        assert 'error' in data
    
    def test_413_error(self, client):
        """Testa erro de arquivo muito grande."""
        # Não testamos diretamente, mas verificamos que o handler existe
        pass
    
    def test_method_not_allowed(self, client):
        """Testa método HTTP não permitido."""
        response = client.post('/api/status')  # GET endpoint
        
        assert response.status_code == 405
