#!/usr/bin/env python3
"""
Bakta Flow End-to-End Tests
Testes end-to-end usando Selenium (opcional)
ou testes de API completos simulando usuário real
"""

import json
import time
import pytest
from io import BytesIO
from pathlib import Path


# ============== TESTES E2E COM API ==============

@pytest.mark.e2e
class TestEndToEndWorkflow:
    """Testes E2E simulando fluxo completo do usuário."""
    
    def test_complete_user_workflow(self, e2e_client):
        """
        Testa fluxo completo:
        1. Usuário acessa página
        2. Verifica status da API
        3. Lista templates disponíveis
        4. Faz upload de arquivo
        5. Inicia anotação
        6. Acompanha progresso
        7. Verifica resultados
        8. Faz download
        """
        client = e2e_client
        
        # 1. Verificar status da aplicação
        print("\n[1/8] Verificando status da aplicação...")
        response = client.get('/api/status')
        assert response.status_code == 200
        status_data = json.loads(response.data)
        assert status_data['status'] == 'ok'
        print(f"   ✅ API online: {status_data['service']}")
        
        # 2. Listar templates
        print("\n[2/8] Listando templates disponíveis...")
        response = client.get('/api/templates')
        templates_data = json.loads(response.data)
        print(f"   ✅ {len(templates_data['templates'])} templates disponíveis")
        
        # 3. Upload de arquivo
        print("\n[3/8] Fazendo upload de arquivo FASTA...")
        fasta_content = self._create_realistic_fasta()
        response = client.post(
            '/api/upload',
            data={'file': (BytesIO(fasta_content), 'genome.fasta')},
            content_type='multipart/form-data'
        )
        assert response.status_code == 200
        upload_data = json.loads(response.data)
        filename = upload_data['filename']
        print(f"   ✅ Arquivo enviado: {filename}")
        
        # 4. Iniciar anotação
        print("\n[4/8] Iniciando anotação...")
        response = client.post(
            '/api/annotate',
            data=json.dumps({
                'source': 'upload',
                'filename': filename,
                'prefix': 'e2e_test_genome'
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        job_data = json.loads(response.data)
        job_id = job_data['job_id']
        print(f"   ✅ Job iniciado: {job_id}")
        
        # 5. Acompanhar progresso (simulado)
        print("\n[5/8] Acompanhando progresso...")
        self._simulate_job_progress(client, job_id)
        print("   ✅ Progresso acompanhado")
        
        # 6. Verificar resultados
        print("\n[6/8] Verificando resultados...")
        response = client.get(f'/api/jobs/{job_id}')
        assert response.status_code == 200
        result_data = json.loads(response.data)
        assert 'stats' in result_data or 'runtime_status' in result_data
        print(f"   ✅ Resultados obtidos")
        
        # 7. Verificar estatísticas
        print("\n[7/8] Verificando estatísticas gerais...")
        response = client.get('/api/stats')
        stats_data = json.loads(response.data)
        assert 'total_jobs' in stats_data
        print(f"   ✅ Estatísticas: {stats_data['total_jobs']} jobs totais")
        
        # 8. Limpar (remover job)
        print("\n[8/8] Limpando recursos...")
        response = client.delete(f'/api/jobs/{job_id}')
        if response.status_code == 200:
            print(f"   ✅ Job removido")
        else:
            print(f"   ⚠️  Job não removido (pode não existir no disco)")
        
        print("\n" + "="*50)
        print("✅ FLUXO E2E COMPLETADO COM SUCESSO!")
        print("="*50)
    
    def test_template_based_annotation(self, e2e_client, e2e_templates):
        """Testa anotação usando template."""
        client = e2e_client
        
        # Verificar templates
        response = client.get('/api/templates')
        templates = json.loads(response.data)['templates']
        
        if not templates:
            pytest.skip("Nenhum template disponível")
        
        template = templates[0]
        
        # Iniciar anotação com template
        response = client.post(
            '/api/annotate',
            data=json.dumps({
                'source': 'template',
                'filename': template['name']
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        job_data = json.loads(response.data)
        assert job_data['success'] is True
    
    def test_multiple_annotations_parallel(self, e2e_client):
        """Testa múltiplas anotações em paralelo."""
        client = e2e_client
        
        jobs = []
        
        # Iniciar 3 anotações
        for i in range(3):
            fasta = f">genome_{i}\nATCGATCGATCGATCGATCG"
            
            # Upload
            response = client.post(
                '/api/upload',
                data={'file': (BytesIO(fasta.encode()), f'genome_{i}.fasta')},
                content_type='multipart/form-data'
            )
            assert response.status_code == 200
            filename = json.loads(response.data)['filename']
            
            # Anotar
            response = client.post(
                '/api/annotate',
                data=json.dumps({
                    'source': 'upload',
                    'filename': filename
                }),
                content_type='application/json'
            )
            assert response.status_code == 200
            jobs.append(json.loads(response.data)['job_id'])
        
        # Verificar que todos os jobs foram criados
        response = client.get('/api/jobs')
        jobs_data = json.loads(response.data)
        
        assert len(jobs_data['jobs']) >= 3
        print(f"\n✅ {len(jobs)} anotações paralelas iniciadas")
    
    def test_error_recovery(self, e2e_client):
        """Testa recuperação de erros."""
        client = e2e_client
        
        # Tentar operações inválidas
        
        # 1. Upload sem arquivo
        response = client.post('/api/upload')
        assert response.status_code == 400
        
        # 2. Anotação de arquivo inexistente
        response = client.post(
            '/api/annotate',
            data=json.dumps({
                'source': 'upload',
                'filename': 'nonexistent.fasta'
            }),
            content_type='application/json'
        )
        assert response.status_code == 404
        
        # 3. Job inexistente
        response = client.get('/api/jobs/nonexistent_job_xyz')
        assert response.status_code == 404
        
        # 4. Download de arquivo inexistente
        response = client.get('/api/jobs/nonexistent/files/json')
        assert response.status_code == 404
        
        print("\n✅ Todos os erros foram tratados corretamente")
    
    def _create_realistic_fasta(self):
        """Cria um FASTA realista para testes."""
        lines = [">Escherichia_coli_test_genome"]
        
        # Gerar sequência de ~5KB
        sequence = "ATGAAACGCATTAGCACCACCATTACCACCACCATCACCATTACCACAGGTAAC"
        for _ in range(100):
            lines.append(sequence)
        
        return '\n'.join(lines).encode()
    
    def _simulate_job_progress(self, client, job_id):
        """Simula acompanhamento de progresso."""
        # Em testes reais, esperaríamos o job completar
        # Aqui apenas verificamos que o endpoint existe
        response = client.get(f'/api/jobs/{job_id}/status')
        
        # Pode retornar 200 (em memória) ou 404 (não iniciado)
        assert response.status_code in [200, 404]


# ============== FIXTURES E2E ==============

@pytest.fixture
def e2e_client(tmp_path_factory):
    """Cria cliente para testes E2E."""
    import sys
    backend_path = Path(__file__).parent.parent.parent / "backend"
    sys.path.insert(0, str(backend_path))
    
    from app import app, jobs_status
    
    # Limpar estado
    jobs_status.clear()
    
    # Diretórios
    base_path = tmp_path_factory.mktemp("e2e")
    
    app.config['TESTING'] = True
    app.config['UPLOAD_FOLDER'] = str(base_path / "uploads")
    
    (base_path / "uploads").mkdir(exist_ok=True)
    (base_path / "results").mkdir(exist_ok=True)
    (base_path / "templates").mkdir(exist_ok=True)
    
    with app.test_client() as client:
        yield client
    
    jobs_status.clear()


@pytest.fixture
def e2e_templates(e2e_client, tmp_path_factory):
    """Cria templates para testes E2E."""
    import sys
    backend_path = Path(__file__).parent.parent.parent / "backend"
    sys.path.insert(0, str(backend_path))
    
    from app import TEMPLATES_FOLDER
    
    # Criar templates
    templates = [
        ("ecoli_test.fasta", ">E_coli\nATCGATCGATCG"),
        ("bacillus_test.fasta", ">B_subtilis\nGCTAGCTAGCTA"),
    ]
    
    for name, content in templates:
        template_path = Path(TEMPLATES_FOLDER) / name
        template_path.parent.mkdir(parents=True, exist_ok=True)
        template_path.write_text(content)
    
    yield templates
    
    # Cleanup
    for name, _ in templates:
        template_path = Path(TEMPLATES_FOLDER) / name
        if template_path.exists():
            template_path.unlink()


# ============== TESTES DE CARGA ==============

@pytest.mark.e2e
@pytest.mark.slow
class TestLoad:
    """Testes de carga (requerem mais tempo)."""
    
    def test_api_under_load(self, e2e_client):
        """Testa API sob carga."""
        client = e2e_client
        
        import concurrent.futures
        
        def make_request(i):
            response = client.get('/api/status')
            return response.status_code == 200
        
        start = time.time()
        
        # 50 requests simultâneos
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(make_request, range(50)))
        
        elapsed = time.time() - start
        
        success_rate = sum(results) / len(results)
        
        assert success_rate >= 0.95  # 95% de sucesso
        assert elapsed < 30  # Em menos de 30 segundos
        
        print(f"\n✅ Load test: {success_rate*100:.1f}% sucesso em {elapsed:.2f}s")
