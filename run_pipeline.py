#!/usr/bin/env python3
"""
Bakta Flow Pipeline Runner
Script para executar o pipeline de anotação
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime

# Adicionar backend ao path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

try:
    from pipeline import BaktaPipeline
except ImportError as e:
    print(f"❌ Erro ao importar pipeline: {e}")
    print("   Verifique se o arquivo backend/pipeline.py existe")
    sys.exit(1)


def print_header(text):
    """Printa header formatado."""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)


def list_available_genomes(templates_dir="data/templates"):
    """Lista genomas disponíveis."""
    templates_path = Path(templates_dir)
    
    if not templates_path.exists():
        print(f"⚠️  Diretório {templates_dir} não encontrado")
        return []
    
    genomes = list(templates_path.glob("*.fasta"))
    return genomes


def run_annotation(input_file, db_path="./bakta-light", output_dir="./resultados", 
                   threads=4, prefix=None, meta_mode=True):
    """Executa anotação em um arquivo."""
    
    print_header("Iniciando Anotação Genômica")
    
    # Verificar arquivo
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"❌ Arquivo não encontrado: {input_file}")
        return False
    
    print(f"📁 Input: {input_path.absolute()}")
    print(f"🧬 Database: {db_path}")
    print(f"📂 Output: {output_dir}")
    print(f"🔧 Threads: {threads}")
    print(f"📊 Meta mode: {meta_mode}")
    
    # Criar pipeline
    pipeline = BaktaPipeline(
        db_path=db_path,
        output_dir=output_dir,
        threads=threads,
        meta_mode=meta_mode
    )
    
    # Verificar dependências
    print("\n🔍 Verificando dependências...")
    
    if not pipeline.check_bakta_installation():
        print("❌ Bakta não está instalado ou não está no PATH!")
        print("\nPara instalar:")
        print("   conda activate bakta_env")
        print("   conda install -c bioconda bakta")
        return False
    
    if not pipeline.check_database():
        print(f"❌ Database não encontrado em: {db_path}")
        print("\nPara baixar:")
        print(f"   bakta_db download --type light --output {db_path}")
        return False
    
    print("✅ Todas as dependências OK!")
    
    # Executar
    print(f"\n🚀 Iniciando anotação...")
    print(f"   Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = time.time()
    
    success, result = pipeline.run_annotation(
        fasta_path=str(input_path),
        prefix=prefix,
        verbose=True
    )
    
    elapsed_time = time.time() - start_time
    
    if success:
        print(f"\n✅ Anotação concluída com sucesso!")
        print(f"   Tempo: {elapsed_time:.2f} segundos")
        print(f"   Job ID: {result['job_id']}")
        print(f"   Diretório: {result['output_dir']}")
        
        if 'stats' in result:
            stats = result['stats']
            print("\n📊 Estatísticas:")
            print(f"   Tamanho do genoma: {stats.get('genome_size', 'N/A'):,} bp")
            print(f"   GC Content: {stats.get('gc_content', 'N/A'):.2f}%")
            print(f"   CDS: {stats.get('cds', 'N/A')}")
            print(f"   Genes: {stats.get('genes', 'N/A')}")
            print(f"   tRNAs: {stats.get('trnas', 'N/A')}")
            print(f"   rRNAs: {stats.get('rrnas', 'N/A')}")
        
        print("\n📁 Arquivos gerados:")
        if 'files' in result:
            for ext, info in result['files'].items():
                print(f"   • .{ext:<6} - {info.get('description', '')}")
        
        return True
    else:
        print(f"\n❌ Erro na anotação!")
        print(f"   {result.get('error', 'Erro desconhecido')}")
        return False


def list_previous_jobs(output_dir="./resultados"):
    """Lista jobs anteriores."""
    print_header("Jobs Anteriores")
    
    pipeline = BaktaPipeline(output_dir=output_dir)
    jobs = pipeline.list_jobs()
    
    if not jobs:
        print("Nenhum job encontrado.")
        return
    
    print(f"\n{'Job ID':<30} {'Status':<12} {'CDS':<8} {'tRNAs':<8}")
    print("-" * 60)
    
    for job in jobs:
        job_id = job.get('job_id', 'N/A')
        status = job.get('status', 'unknown')
        stats = job.get('stats', {})
        cds = stats.get('cds', 0)
        trnas = stats.get('trnas', 0)
        
        status_icon = {
            'completed': '✅',
            'error': '❌',
            'running': '⏳'
        }.get(status, '❓')
        
        print(f"{job_id:<30} {status_icon} {status:<10} {cds:<8} {trnas:<8}")


def show_job_details(job_id, output_dir="./resultados"):
    """Mostra detalhes de um job."""
    print_header(f"Detalhes do Job: {job_id}")
    
    pipeline = BaktaPipeline(output_dir=output_dir)
    job = pipeline.get_job(job_id)
    
    if not job:
        print(f"❌ Job não encontrado: {job_id}")
        return
    
    print(f"\n📋 Informações Gerais:")
    print(f"   Job ID: {job['job_id']}")
    print(f"   Status: {job.get('status', 'unknown')}")
    print(f"   Prefixo: {job.get('prefix', 'N/A')}")
    print(f"   Diretório: {job.get('output_dir', 'N/A')}")
    
    if 'stats' in job:
        print(f"\n📊 Estatísticas:")
        for key, value in job['stats'].items():
            print(f"   {key}: {value}")
    
    if 'files' in job:
        print(f"\n📁 Arquivos:")
        for ext, info in job['files'].items():
            size = info.get('size', 0)
            size_str = f"{size:,} bytes" if size else "N/A"
            print(f"   .{ext:<6} - {size_str}")


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description="Bakta Flow Pipeline Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Anotar um arquivo FASTA
  python run_pipeline.py --input genome.fasta
  
  # Usar template
  python run_pipeline.py --input data/templates/ecoli_k12.fasta
  
  # Listar jobs anteriores
  python run_pipeline.py --list
  
  # Ver detalhes de um job
  python run_pipeline.py --show-job 20260314_120000_abc123
  
  # Opções avançadas
  python run_pipeline.py --input genome.fasta --threads 8 --prefix my_genome
        """
    )
    
    parser.add_argument(
        "--input", "-i",
        help="Arquivo FASTA para anotação"
    )
    parser.add_argument(
        "--db", "-d",
        default="./bakta-light",
        help="Caminho para o database Bakta (default: ./bakta-light)"
    )
    parser.add_argument(
        "--output", "-o",
        default="./resultados",
        help="Diretório de saída (default: ./resultados)"
    )
    parser.add_argument(
        "--threads", "-t",
        type=int,
        default=4,
        help="Número de threads (default: 4)"
    )
    parser.add_argument(
        "--prefix", "-p",
        help="Prefixo para arquivos de saída"
    )
    parser.add_argument(
        "--no-meta",
        action="store_true",
        help="Desativar modo metagenoma"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="Listar jobs anteriores"
    )
    parser.add_argument(
        "--show-job",
        metavar="JOB_ID",
        help="Mostrar detalhes de um job específico"
    )
    parser.add_argument(
        "--templates",
        action="store_true",
        help="Listar templates disponíveis"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("  🧬 Bakta Flow Pipeline")
    print("="*60)
    
    # Listar templates
    if args.templates:
        print_header("Templates Disponíveis")
        templates = list_available_genomes()
        
        if templates:
            for i, template in enumerate(templates, 1):
                size = template.stat().st_size
                print(f"  {i}. {template.name:<30} ({size:,} bytes)")
        else:
            print("  Nenhum template encontrado em data/templates/")
        return
    
    # Listar jobs
    if args.list:
        list_previous_jobs(args.output)
        return
    
    # Mostrar job
    if args.show_job:
        show_job_details(args.show_job, args.output)
        return
    
    # Executar anotação
    if args.input:
        success = run_annotation(
            input_file=args.input,
            db_path=args.db,
            output_dir=args.output,
            threads=args.threads,
            prefix=args.prefix,
            meta_mode=not args.no_meta
        )
        
        sys.exit(0 if success else 1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
