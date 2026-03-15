#!/usr/bin/env python3
"""
PUC Minas - Bakta Web API
API Flask para interface web de anotação genômica
"""

import os
import json
import uuid
import shutil
from pathlib import Path
from datetime import datetime
from functools import wraps
from threading import Thread

from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename

from pipeline import BaktaPipeline

# Configurações
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_FOLDER = BASE_DIR / "data" / "uploads"
RESULTS_FOLDER = BASE_DIR / "resultados"
TEMPLATES_FOLDER = BASE_DIR / "data" / "templates"
ALLOWED_EXTENSIONS = {'fasta', 'fna', 'fa', 'fas'}
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB

# Criar diretórios
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)
TEMPLATES_FOLDER.mkdir(parents=True, exist_ok=True)

# Inicializar Flask
app = Flask(
    __name__,
    template_folder=str(BASE_DIR / 'frontend'),
    static_folder=str(BASE_DIR / 'frontend' / 'static')
)
app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Habilitar CORS
CORS(app)

# Armazenamento de jobs em memória (em produção, use Redis/DB)
jobs_status = {}


def allowed_file(filename):
    """Verifica se a extensão do arquivo é permitida."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db_path():
    """Obtém o caminho do database Bakta."""
    # Prioridade: variável de ambiente > padrão
    db_path = os.environ.get('BAKTA_DB', './bakta-light')
    return db_path


def run_annotation_async(job_id: str, fasta_path: str, prefix: str):
    """Executa anotação em thread separada."""
    try:
        jobs_status[job_id] = {
            "status": "running",
            "progress": 0,
            "message": "Iniciando anotação...",
            "started_at": datetime.now().isoformat()
        }
        
        meta_mode_enabled = os.environ.get("BAKTA_META_MODE", "false").lower() in {
            "1", "true", "yes", "on"
        }

        pipeline = BaktaPipeline(
            db_path=get_db_path(),
            output_dir=str(RESULTS_FOLDER),
            threads=4,
            meta_mode=meta_mode_enabled
        )
        
        jobs_status[job_id]["progress"] = 10
        jobs_status[job_id]["message"] = "Executando Bakta..."
        
        success, result = pipeline.run_annotation(
            fasta_path=fasta_path,
            job_id=job_id,
            prefix=prefix,
            verbose=False
        )
        
        if success:
            jobs_status[job_id].update({
                "status": "completed",
                "progress": 100,
                "message": "Anotação concluída!",
                "completed_at": datetime.now().isoformat(),
                "result": result
            })
        else:
            jobs_status[job_id].update({
                "status": "error",
                "progress": 0,
                "message": result.get("error", "Erro desconhecido"),
                "completed_at": datetime.now().isoformat()
            })
            
    except Exception as e:
        jobs_status[job_id].update({
            "status": "error",
            "progress": 0,
            "message": str(e),
            "completed_at": datetime.now().isoformat()
        })


# ============== ROTAS DA API ==============

@app.route('/')
def index():
    """Página principal."""
    return render_template('index.html')


@app.route('/api/status')
def api_status():
    """Verifica status da API."""
    return jsonify({
        "status": "ok",
        "service": "PUC Minas - Bakta API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/templates')
def list_templates():
    """Lista templates de genomas disponíveis."""
    templates = []
    
    if TEMPLATES_FOLDER.exists():
        for file_path in TEMPLATES_FOLDER.iterdir():
            if file_path.is_file() and allowed_file(file_path.name):
                templates.append({
                    "id": file_path.stem,
                    "name": file_path.name,
                    "size": file_path.stat().st_size,
                    "path": str(file_path)
                })
    
    return jsonify({
        "templates": sorted(templates, key=lambda x: x["name"])
    })


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Faz upload de arquivo FASTA."""
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Adicionar timestamp para evitar conflitos
        unique_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        file_path = UPLOAD_FOLDER / unique_name
        file.save(file_path)
        
        return jsonify({
            "success": True,
            "filename": unique_name,
            "original_name": filename,
            "path": str(file_path),
            "size": file_path.stat().st_size
        })
    
    return jsonify({
        "error": "Tipo de arquivo não permitido. Use: .fasta, .fna, .fa, .fas"
    }), 400


@app.route('/api/annotate', methods=['POST'])
def start_annotation():
    """Inicia processo de anotação."""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Dados não fornecidos"}), 400
    
    # Determinar fonte do FASTA
    source = data.get('source', 'upload')  # 'upload' ou 'template'
    filename = data.get('filename')
    prefix = data.get('prefix')
    
    if not filename:
        return jsonify({"error": "Nome do arquivo não fornecido"}), 400
    
    # Determinar caminho do arquivo
    if source == 'template':
        fasta_path = TEMPLATES_FOLDER / filename
    else:
        fasta_path = UPLOAD_FOLDER / filename
    
    if not fasta_path.exists():
        return jsonify({"error": f"Arquivo não encontrado: {filename}"}), 404

    # Validar prontidão do DB antes de iniciar thread de anotação.
    precheck_pipeline = BaktaPipeline(
        db_path=get_db_path(),
        output_dir=str(RESULTS_FOLDER)
    )
    if not precheck_pipeline.check_database():
        return jsonify({
            "error": "Database Bakta ainda não está pronto. Aguarde o download/conclusão e tente novamente."
        }), 503
    
    # Gerar job ID
    job_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]
    
    # Definir prefixo
    if not prefix:
        prefix = Path(filename).stem
    
    # Iniciar anotação em thread separada
    thread = Thread(
        target=run_annotation_async,
        args=(job_id, str(fasta_path), prefix)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "success": True,
        "job_id": job_id,
        "status": "started",
        "message": "Anotação iniciada"
    })


@app.route('/api/jobs')
def list_jobs():
    """Lista todos os jobs."""
    pipeline = BaktaPipeline(
        db_path=get_db_path(),
        output_dir=str(RESULTS_FOLDER)
    )
    
    jobs = pipeline.list_jobs()
    
    # Atualizar com status em memória
    for job in jobs:
        job_id = job.get("job_id")
        if job_id in jobs_status:
            job["runtime_status"] = jobs_status[job_id]
    
    return jsonify({
        "jobs": jobs,
        "total": len(jobs)
    })


@app.route('/api/jobs/<job_id>')
def get_job(job_id):
    """Obtém detalhes de um job."""
    pipeline = BaktaPipeline(
        db_path=get_db_path(),
        output_dir=str(RESULTS_FOLDER)
    )
    
    job = pipeline.get_job(job_id)
    
    if job:
        # Adicionar status em memória se existir
        if job_id in jobs_status:
            job["runtime_status"] = jobs_status[job_id]
        return jsonify(job)
    
    # Verificar se existe apenas em memória (job em andamento)
    if job_id in jobs_status:
        return jsonify({
            "job_id": job_id,
            "status": "pending",
            "runtime_status": jobs_status[job_id]
        })
    
    return jsonify({"error": "Job não encontrado"}), 404


@app.route('/api/jobs/<job_id>/status')
def get_job_status(job_id):
    """Obtém status de um job."""
    if job_id in jobs_status:
        return jsonify(jobs_status[job_id])
    
    # Verificar no disco
    pipeline = BaktaPipeline(
        db_path=get_db_path(),
        output_dir=str(RESULTS_FOLDER)
    )
    
    job = pipeline.get_job(job_id)
    if job:
        return jsonify({
            "status": job.get("status", "unknown"),
            "result": job
        })
    
    return jsonify({"error": "Job não encontrado"}), 404


@app.route('/api/jobs/<job_id>/files/<file_type>')
def download_file(job_id, file_type):
    """Download de arquivo de resultado."""
    job_dir = RESULTS_FOLDER / job_id
    
    if not job_dir.exists():
        return jsonify({"error": "Job não encontrado"}), 404
    
    # Encontrar arquivo pelo tipo
    for file_path in job_dir.iterdir():
        if file_path.suffix == f".{file_type}" or file_path.name.endswith(f".{file_type}"):
            return send_file(
                file_path,
                as_attachment=True,
                download_name=file_path.name
            )
    
    return jsonify({"error": f"Arquivo do tipo '{file_type}' não encontrado"}), 404


@app.route('/api/jobs/<job_id>', methods=['DELETE'])
def delete_job(job_id):
    """Remove um job."""
    pipeline = BaktaPipeline(
        db_path=get_db_path(),
        output_dir=str(RESULTS_FOLDER)
    )
    
    if pipeline.delete_job(job_id):
        # Remover do status em memória
        if job_id in jobs_status:
            del jobs_status[job_id]
        return jsonify({"success": True, "message": "Job removido"})
    
    return jsonify({"error": "Job não encontrado"}), 404


@app.route('/api/stats')
def get_stats():
    """Obtém estatísticas gerais."""
    pipeline = BaktaPipeline(
        db_path=get_db_path(),
        output_dir=str(RESULTS_FOLDER)
    )
    
    jobs = pipeline.list_jobs()
    
    completed = sum(1 for j in jobs if j.get("status") == "completed")
    errors = sum(1 for j in jobs if j.get("status") == "error")
    
    total_cds = sum(
        j.get("stats", {}).get("cds", 0) 
        for j in jobs if j.get("status") == "completed"
    )
    
    return jsonify({
        "total_jobs": len(jobs),
        "completed": completed,
        "errors": errors,
        "total_cds_annotated": total_cds
    })


@app.route('/api/bakta/check')
def check_bakta():
    """Verifica instalação do Bakta."""
    pipeline = BaktaPipeline(db_path=get_db_path())
    
    installed = pipeline.check_bakta_installation()
    db_exists = pipeline.check_database()
    
    return jsonify({
        "bakta_installed": installed,
        "database_exists": db_exists,
        "database_path": str(pipeline.db_path)
    })


# ============== ERROR HANDLERS ==============

@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "Arquivo muito grande (max: 100MB)"}), 413


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Recurso não encontrado"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Erro interno do servidor"}), 500


# ============== MAIN ==============

if __name__ == '__main__':
    print("="*60)
    print("PUC Minas - Bakta Web API")
    print("="*60)
    print(f"Upload folder: {UPLOAD_FOLDER}")
    print(f"Results folder: {RESULTS_FOLDER}")
    print(f"Database path: {get_db_path()}")
    print("="*60)
    
    # Verificar Bakta
    pipeline = BaktaPipeline(db_path=get_db_path())
    if not pipeline.check_bakta_installation():
        print("⚠️  AVISO: Bakta não encontrado no PATH")
        print("    Instale com: conda activate bakta_env")
    else:
        print("✅ Bakta instalado")
    
    if not pipeline.check_database():
        print("⚠️  AVISO: Database não encontrado")
        print(f"    Esperado em: {pipeline.db_path}")
        print("    Baixe com: bakta_db download --type light --output ./bakta-light")
    else:
        print("✅ Database encontrado")
    
    print("="*60)
    print("Servidor iniciado em http://localhost:5000")
    print("="*60)
    
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=debug_mode,
        use_reloader=debug_mode,
        threaded=True
    )
