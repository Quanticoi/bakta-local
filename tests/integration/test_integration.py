#!/usr/bin/env python3
"""
Bakta Flow Integration Tests
Testes de integração para o sistema completo
"""

import json
import time
import pytest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch, MagicMock


# ============== FIXTURES DE INTEGRAÇÃO ==============

@pytest.fixture
def integration_client(tmp_path):
    """Cria cliente de teste com diretórios temporários."""
    import sys
    backend_path = Path(__file__).parent.parent.parent / "backend"
    sys.path.insert(0, str(backend_path))
    
    from app import app, jobs_status
    
    # Limpar jobs_status
    jobs_status.clear()
    
    # Configurar diretórios temporários
    app.config['TESTING'] = True
    app.config['UPLOAD_FOLDER'] = str(tmp_path / "uploads")
    
    # Criar diretórios
    (tmp_path / "uploads").mkdir(exist_ok=True)
    (tmp_path / "results").mkdir(exist_ok=True)
    (tmp_path / "templates").mkdir(exist_ok=True)
    
    with app.test_client() as client:
        yield client, tmp_path
    
    # Cleanup
    jobs_status.clear()


# ============== TESTES DE FLUXO COMPLETO ==============

@pytest.mark.integration
class TestFullWorkflow:
    """Testes de fluxo completo da aplicação."""
    
    def test_upload_and_annotate_workflow(self, integration_client):
        """Testa fluxo completo: upload → anotação → status → download."""
        client, tmp_path = integration_client
        
        # 1. Upload
        fasta_content = """>test_genome
ATGAAACGCATTAGCACCACCATTACCACCACCATCACCATTACCACAGGTAACGGTGCGGGCTGA
ATGAAACGCATTAGCACCACCATTACCACCACCATCACCATTACCACAGGTAACGGTGCGGGCTGA
"""
        response = client.post(
            '/api/upload',
            data={'file': (BytesIO(fasta_content.encode()), 'test.fasta')},
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 200
        upload_data = json.loads(response.data)
        assert upload_data['success'] is True
        filename = upload_data['filename']
        
        # 2. Iniciar anotação (mock do processo async)
        with patch('app.Thread') as mock_thread:
            mock_thread_instance = MagicMock()
            mock_thread.return_value = mock_thread_instance
            
            response = client.post(
                '/api/annotate',
                data=json.dumps({
                    'source': 'upload',
                    'filename': filename,
                    'prefix': 'test_integration'
                }),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            annotate_data = json.loads(response.data)
            assert annotate_data['success'] is True
            job_id = annotate_data['job_id']
            
            # Verificar que thread foi iniciada
            mock_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()
        
        # 3. Verificar status (inicialmente em memória)
        response = client.get(f'/api/jobs/{job_id}/status')
        
        # 4. Listar jobs
        response = client.get('/api/jobs')
        
        assert response.status_code == 200
        jobs_data = json.loads(response.data)
        assert 'jobs' in jobs_data
    
    def test_template_annotate_workflow(self, integration_client):
        """Testa fluxo completo com template."""
        client, tmp_path = integration_client
        
        # Criar template
        template_file = tmp_path / "templates" / "ecoli.fasta"
        template_file.write_text(">ecoli\nATCGATCGATCGATCGATCG")
        
        with patch('app.TEMPLATES_FOLDER', tmp_path / "templates"):
            # 1. Listar templates
            response = client.get('/api/templates')
            
            assert response.status_code == 200
            templates_data = json.loads(response.data)
            assert len(templates_data['templates']) == 1
            
            # 2. Anotar template
            with patch('app.Thread'):
                response = client.post(
                    '/api/annotate',
                    data=json.dumps({
                        'source': 'template',
                        'filename': 'ecoli.fasta'
                    }),
                    content_type='application/json'
                )
                
                assert response.status_code == 200


# ============== TESTES DE API COMPLETA ==============

@pytest.mark.integration
class TestApiIntegration:
    """Testes de integração da API."""
    
    def test_api_status_endpoint(self, integration_client):
        """Testa endpoint de status."""
        client, _ = integration_client
        
        response = client.get('/api/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['status'] == 'ok'
        assert 'service' in data
        assert 'version' in data
        assert 'timestamp' in data
    
    def test_concurrent_uploads(self, integration_client):
        """Testa múltiplos uploads simultâneos."""
        client, tmp_path = integration_client
        
        files = []
        for i in range(3):
            response = client.post(
                '/api/upload',
                data={
                    'file': (
                        BytesIO(f'>genome_{i}\nATCGATCGATCG'.encode()),
                        f'genome_{i}.fasta'
                    )
                },
                content_type='multipart/form-data'
            )
            
            assert response.status_code == 200
            files.append(json.loads(response.data))
        
        # Verificar que todos foram salvos
        assert len(files) == 3
        upload_dir = Path(client.application.config['UPLOAD_FOLDER'])
        assert len(list(upload_dir.glob('*.fasta'))) == 3
    
    def test_error_handling_integration(self, integration_client):
        """Testa tratamento de erros em fluxo completo."""
        client, _ = integration_client
        
        # Tentar anotar arquivo inexistente
        response = client.post(
            '/api/annotate',
            data=json.dumps({
                'source': 'upload',
                'filename': 'nonexistent.fasta'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data


# ============== TESTES DE PERSISTÊNCIA ==============

@pytest.mark.integration
class TestPersistence:
    """Testes de persistência de dados."""
    
    def test_job_summary_saved(self, integration_client):
        """Testa se resumo do job é salvo corretamente."""
        client, tmp_path = integration_client
        
        # Criar estrutura de job manualmente
        job_id = "20260314_120000_test_persist"
        job_dir = tmp_path / "results" / job_id
        job_dir.mkdir(parents=True)
        
        summary = {
            "job_id": job_id,
            "status": "completed",
            "stats": {"cds": 100}
        }
        
        summary_file = job_dir / "job_summary.json"
        summary_file.write_text(json.dumps(summary))
        
        # Verificar via API
        with patch('app.RESULTS_FOLDER', tmp_path / "results"):
            response = client.get(f'/api/jobs/{job_id}')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['job_id'] == job_id
            assert data['stats']['cds'] == 100


# ============== TESTES DE PERFORMANCE ==============

@pytest.mark.integration
@pytest.mark.slow
class TestPerformance:
    """Testes de performance (lentos)."""
    
    def test_large_file_upload(self, integration_client):
        """Testa upload de arquivo grande."""
        client, tmp_path = integration_client
        
        # Criar arquivo de 1MB
        large_content = BytesIO()
        large_content.write(b'>large_genome\n')
        large_content.write(b'ATCG' * (1024 * 1024 // 4))  # ~1MB
        large_content.seek(0)
        
        start_time = time.time()
        
        response = client.post(
            '/api/upload',
            data={'file': (large_content, 'large.fasta')},
            content_type='multipart/form-data'
        )
        
        elapsed = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed < 10  # Deve completar em menos de 10 segundos
    
    def test_api_response_time(self, integration_client):
        """Testa tempo de resposta da API."""
        client, _ = integration_client
        
        start_time = time.time()
        
        for _ in range(10):
            response = client.get('/api/status')
            assert response.status_code == 200
        
        elapsed = time.time() - start_time
        avg_time = elapsed / 10
        
        assert avg_time < 0.1  # Média de 100ms por request


# ============== TESTES DE SEGURANÇA ==============

@pytest.mark.integration
class TestSecurity:
    """Testes de segurança."""
    
    def test_path_traversal_upload(self, integration_client):
        """Testa proteção contra path traversal no upload."""
        client, _ = integration_client
        
        response = client.post(
            '/api/upload',
            data={
                'file': (
                    BytesIO(b'>test\nATCG'),
                    '../../../etc/passwd.fasta'  # Tentativa de path traversal
                )
            },
            content_type='multipart/form-data'
        )
        
        # O werkzeug deve sanitizar o nome
        assert response.status_code == 200
        data = json.loads(response.data)
        # Nome deve estar sanitizado (sem ../)
        assert '..' not in data['filename']
    
    def test_large_payload_rejection(self, integration_client):
        """Testa rejeição de payload muito grande."""
        client, _ = integration_client
        
        # Tentar upload de arquivo muito grande (> 100MB)
        huge_content = BytesIO(b'x' * (101 * 1024 * 1024))
        
        response = client.post(
            '/api/upload',
            data={'file': (huge_content, 'huge.fasta')},
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 413  # Payload Too Large
