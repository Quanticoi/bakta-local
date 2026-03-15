#!/usr/bin/env python3
"""
PUC Minas - Bakta Pipeline
Pipeline de execução para anotação genômica com Bakta
"""

import os
import json
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BaktaPipeline:
    """Pipeline de anotação genômica usando Bakta."""
    
    def __init__(
        self,
        db_path: str = "./bakta-light",
        output_dir: str = "./resultados",
        threads: int = 4,
        meta_mode: bool = True
    ):
        """
        Inicializa o pipeline Bakta.
        
        Args:
            db_path: Caminho para o database Bakta
            output_dir: Diretório de saída dos resultados
            threads: Número de threads para processamento
            meta_mode: Modo metagenoma (mais tolerante)
        """
        self.db_path = Path(db_path).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.threads = threads
        self.meta_mode = meta_mode
        
        # Criar diretório de resultados se não existir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Pipeline inicializado: db={self.db_path}, output={self.output_dir}")

    def _resolve_db_path(self) -> Optional[Path]:
        """Resolve caminho real do DB, aceitando estrutura com subpasta `db`."""
        candidates = [
            self.db_path,
            self.db_path / "db",
            self.db_path / "db-light"
        ]

        for candidate in candidates:
            if (candidate / "version.json").exists():
                return candidate

        return None
    
    def check_bakta_installation(self) -> bool:
        """Verifica se o Bakta está instalado e acessível."""
        try:
            result = subprocess.run(
                ["bakta", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.info(f"Bakta encontrado: {result.stdout.strip()}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        logger.error("Bakta não encontrado no PATH")
        return False
    
    def check_database(self) -> bool:
        """Verifica se o database está pronto para uso."""
        resolved_db = self._resolve_db_path()
        if resolved_db is None:
            logger.error(
                f"Database não pronto em: {self.db_path} (version.json ausente)"
            )
            return False

        # Atualiza para caminho efetivo do DB caso esteja em subdiretório.
        self.db_path = resolved_db
        logger.info(f"Database encontrado: {self.db_path}")
        return True
    
    def create_job_dir(self, job_id: str) -> Path:
        """Cria diretório para um job específico."""
        job_dir = self.output_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        return job_dir
    
    def run_annotation(
        self,
        fasta_path: str,
        job_id: Optional[str] = None,
        prefix: Optional[str] = None,
        verbose: bool = True
    ) -> Tuple[bool, Dict]:
        """
        Executa a anotação genômica com Bakta.
        
        Args:
            fasta_path: Caminho para o arquivo FASTA
            job_id: ID do job (gerado automaticamente se não fornecido)
            prefix: Prefixo para os arquivos de saída
            verbose: Mostrar saída detalhada
            
        Returns:
            Tuple (sucesso, resultado_dict)
        """
        fasta_path = Path(fasta_path).resolve()
        
        # Validações
        if not fasta_path.exists():
            return False, {"error": f"Arquivo FASTA não encontrado: {fasta_path}"}
        
        if not self.check_bakta_installation():
            return False, {"error": "Bakta não instalado"}

        if not self.check_database():
            return False, {"error": "Database Bakta não está pronto"}
        
        # Gerar job_id se não fornecido
        if job_id is None:
            job_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if prefix is None:
            prefix = fasta_path.stem
        
        # Criar diretório do job
        job_dir = self.create_job_dir(job_id)
        
        # Arquivo de log
        log_file = job_dir / "pipeline.log"
        
        # Construir comando Bakta
        cmd = [
            "bakta",
            "--db", str(self.db_path),
            "--output", str(job_dir),
            "--prefix", prefix,
            "--threads", str(self.threads),
            "--force"
        ]
        
        if self.meta_mode:
            cmd.append("--meta")
        
        # Adicionar opções de saída
        cmd.extend([
            "--genus", "Unknown",
            "--species", "sp."
        ])
        
        cmd.append(str(fasta_path))
        
        logger.info(f"Executando: {' '.join(cmd)}")
        
        # Executar Bakta
        try:
            with open(log_file, 'w') as log:
                log.write(f"Job ID: {job_id}\n")
                log.write(f"Comando: {' '.join(cmd)}\n")
                log.write(f"Início: {datetime.now().isoformat()}\n\n")
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                
                # Capturar saída em tempo real
                output_lines = []
                for line in process.stdout:
                    output_lines.append(line)
                    log.write(line)
                    log.flush()
                    if verbose:
                        print(line, end='')
                
                process.wait()
                
                log.write(f"\nFim: {datetime.now().isoformat()}\n")
                log.write(f"Return code: {process.returncode}\n")
            
            if process.returncode == 0:
                logger.info(f"Anotação concluída com sucesso: {job_id}")
                result = self._parse_results(job_dir, prefix, job_id)
                return True, result
            else:
                error_msg = f"Bakta falhou com código {process.returncode}"
                logger.error(error_msg)
                return False, {"error": error_msg, "job_id": job_id}
                
        except Exception as e:
            logger.exception("Erro durante execução do Bakta")
            return False, {"error": str(e), "job_id": job_id}
    
    def _parse_results(self, job_dir: Path, prefix: str, job_id: str) -> Dict:
        """Parseia os resultados da anotação."""
        result = {
            "job_id": job_id,
            "status": "completed",
            "output_dir": str(job_dir),
            "prefix": prefix,
            "files": {},
            "stats": {}
        }
        
        # Mapear arquivos de saída
        extensions = {
            "gff3": "Anotação GFF3",
            "faa": "Proteínas traduzidas (FASTA)",
            "ffn": "Features nucleotídicas (FASTA)",
            "fna": "Sequências nucleotídicas (FASTA)",
            "gbff": "GenBank",
            "json": "Resultados JSON",
            "txt": "Resumo",
            "tsv": "Features TSV",
            "png": "Visualização circular (PNG)",
            "svg": "Visualização circular"
        }
        
        for ext, description in extensions.items():
            file_path = job_dir / f"{prefix}.{ext}"
            if file_path.exists():
                result["files"][ext] = {
                    "path": str(file_path),
                    "description": description,
                    "size": file_path.stat().st_size
                }
        
        # Extrair estatísticas do JSON se disponível
        json_file = job_dir / f"{prefix}.json"
        if json_file.exists():
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)

                stats = data.get("stats", {})
                features = data.get("features", [])
                sequences = data.get("sequences", [])

                feature_counts = {
                    "cds": 0,
                    "trna": 0,
                    "rrna": 0,
                    "ncrna": 0,
                    "tmrna": 0,
                    "gap": 0,
                    "ori": 0,
                    "pseudo": 0
                }

                for feature in features:
                    ftype = str(feature.get("type", "")).lower()
                    if ftype == "cds":
                        feature_counts["cds"] += 1
                    elif ftype == "trna":
                        feature_counts["trna"] += 1
                    elif ftype == "rrna":
                        feature_counts["rrna"] += 1
                    elif ftype in {"ncrna", "ncrna-region"}:
                        feature_counts["ncrna"] += 1
                    elif ftype == "tmrna":
                        feature_counts["tmrna"] += 1
                    elif ftype == "gap":
                        feature_counts["gap"] += 1
                    elif ftype.startswith("ori"):
                        feature_counts["ori"] += 1
                    elif ftype == "pseudogene":
                        feature_counts["pseudo"] += 1

                gc_fraction_or_pct = stats.get("gc", 0)
                gc_percent = (
                    gc_fraction_or_pct * 100
                    if isinstance(gc_fraction_or_pct, (int, float)) and gc_fraction_or_pct <= 1
                    else gc_fraction_or_pct
                )

                result["stats"] = {
                    "genome_size": stats.get("genome_size", stats.get("size", 0)),
                    "gc_content": gc_percent or 0,
                    "n_contigs": stats.get("n_contigs", len(sequences)),
                    "n50": stats.get("n50", 0),
                    "cds": stats.get("feature_cds", feature_counts["cds"]),
                    "genes": stats.get("feature_gene", feature_counts["cds"]),
                    "trnas": stats.get("feature_trna", feature_counts["trna"]),
                    "rrnas": stats.get("feature_rrna", feature_counts["rrna"]),
                    "ncrnas": stats.get("feature_ncrna", feature_counts["ncrna"]),
                    "tmrnas": stats.get("feature_tmrna", feature_counts["tmrna"]),
                    "pus": stats.get("feature_pseudo", feature_counts["pseudo"]),
                    "oris": stats.get("feature_ori", feature_counts["ori"]),
                    "gap": stats.get("feature_gap", feature_counts["gap"])
                }
            except Exception as e:
                logger.warning(f"Erro ao parsear JSON: {e}")
        
        # Salvar resumo do job
        summary_file = job_dir / "job_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result
    
    def list_jobs(self) -> List[Dict]:
        """Lista todos os jobs executados."""
        jobs = []
        
        if not self.output_dir.exists():
            return jobs
        
        for job_dir in self.output_dir.iterdir():
            if job_dir.is_dir():
                summary_file = job_dir / "job_summary.json"
                if summary_file.exists():
                    try:
                        with open(summary_file, 'r') as f:
                            job = json.load(f)
                            jobs.append(job)
                    except Exception as e:
                        logger.warning(f"Erro ao ler {summary_file}: {e}")
                else:
                    # Job em andamento ou incompleto
                    jobs.append({
                        "job_id": job_dir.name,
                        "status": "unknown",
                        "output_dir": str(job_dir)
                    })
        
        return sorted(jobs, key=lambda x: x.get("job_id", ""), reverse=True)
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """Obtém detalhes de um job específico."""
        job_dir = self.output_dir / job_id
        summary_file = job_dir / "job_summary.json"
        
        if summary_file.exists():
            try:
                with open(summary_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erro ao ler job {job_id}: {e}")
        
        return None
    
    def delete_job(self, job_id: str) -> bool:
        """Remove um job e seus arquivos."""
        job_dir = self.output_dir / job_id
        
        if job_dir.exists():
            try:
                shutil.rmtree(job_dir)
                logger.info(f"Job removido: {job_id}")
                return True
            except Exception as e:
                logger.error(f"Erro ao remover job {job_id}: {e}")
        
        return False


# Funções utilitárias para CLI
def main():
    """Função principal para execução via CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="PUC Minas - Bakta Pipeline"
    )
    parser.add_argument(
        "fasta",
        help="Arquivo FASTA para anotação"
    )
    parser.add_argument(
        "--db",
        default="./bakta-light",
        help="Caminho para o database Bakta"
    )
    parser.add_argument(
        "--output",
        default="./resultados",
        help="Diretório de saída"
    )
    parser.add_argument(
        "--job-id",
        help="ID do job (auto-gerado se não fornecido)"
    )
    parser.add_argument(
        "--prefix",
        help="Prefixo dos arquivos de saída"
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=4,
        help="Número de threads"
    )
    parser.add_argument(
        "--no-meta",
        action="store_true",
        help="Desativar modo metagenoma"
    )
    parser.add_argument(
        "--list-jobs",
        action="store_true",
        help="Listar jobs anteriores"
    )
    
    args = parser.parse_args()
    
    # Inicializar pipeline
    pipeline = BaktaPipeline(
        db_path=args.db,
        output_dir=args.output,
        threads=args.threads,
        meta_mode=not args.no_meta
    )
    
    # Listar jobs
    if args.list_jobs:
        jobs = pipeline.list_jobs()
        print(f"\n{'Job ID':<25} {'Status':<12} {'CDS':<8} {'tRNAs':<8} {'rRNAs':<8}")
        print("-" * 65)
        for job in jobs:
            stats = job.get("stats", {})
            print(f"{job.get('job_id', 'N/A'):<25} "
                  f"{job.get('status', 'unknown'):<12} "
                  f"{stats.get('cds', 0):<8} "
                  f"{stats.get('trnas', 0):<8} "
                  f"{stats.get('rrnas', 0):<8}")
        return
    
    # Executar anotação
    success, result = pipeline.run_annotation(
        fasta_path=args.fasta,
        job_id=args.job_id,
        prefix=args.prefix
    )
    
    if success:
        print("\n" + "="*60)
        print("ANOTAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*60)
        print(f"Job ID: {result['job_id']}")
        print(f"Diretório: {result['output_dir']}")
        print("\nEstatísticas:")
        stats = result.get("stats", {})
        print(f"  Tamanho do genoma: {stats.get('genome_size', 0):,} bp")
        print(f"  GC content: {stats.get('gc_content', 0):.2f}%")
        print(f"  CDS: {stats.get('cds', 0)}")
        print(f"  Genes: {stats.get('genes', 0)}")
        print(f"  tRNAs: {stats.get('trnas', 0)}")
        print(f"  rRNAs: {stats.get('rrnas', 0)}")
        print(f"  ncRNAs: {stats.get('ncrnas', 0)}")
    else:
        print("\n" + "="*60)
        print("ERRO NA ANOTAÇÃO")
        print("="*60)
        print(f"Erro: {result.get('error', 'Erro desconhecido')}")


if __name__ == "__main__":
    main()
