#!/usr/bin/env python3
"""
Bakta Flow Pipeline Demo
Demonstração do pipeline em modo simulação (sem Bakta instalado)
"""

import os
import sys
import json
import time
import shutil
from pathlib import Path
from datetime import datetime


def print_header(text):
    """Printa header formatado."""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)


def simulate_bakta_execution(input_file, output_dir, prefix, threads=4):
    """Simula a execução do Bakta."""
    
    print(f"\nIniciando anotacao...")
    print(f"   Arquivo: {input_file}")
    print(f"   Threads: {threads}")
    print(f"   Prefixo: {prefix}")
    print()
    
    # Simular progresso
    steps = [
        ("Lendo arquivo FASTA", 10),
        ("Calculando estatísticas do genoma", 20),
        ("Executando Prodigal (predição de CDS)", 40),
        ("Executando tRNAscan-SE", 60),
        ("Executando INFERNAL (ncRNA)", 75),
        ("Executando Diamond (homologia)", 85),
        ("Executando AMRFinderPlus", 90),
        ("Gerando arquivos de saída", 95),
        ("Finalizando", 100)
    ]
    
    for step, progress in steps:
        print(f"   [{progress:3}%] {step}...")
        time.sleep(0.5)  # Simular trabalho
    
    print()
    
    # Criar arquivos de saída simulados
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Dados simulados
    genome_size = 4639675
    gc_content = 50.79
    cds_count = 4243
    trna_count = 89
    rrna_count = 22
    
    # Criar JSON
    bakta_result = {
        "version": "1.9.4-demo",
        "genome": {
            "genus": "Escherichia",
            "species": "coli",
            "strain": "K-12-demo",
            "complete": True
        },
        "stats": {
            "genome_size": genome_size,
            "gc": gc_content,
            "n_contigs": 1,
            "n50": genome_size,
            "feature_cds": cds_count,
            "feature_gene": cds_count,
            "feature_trna": trna_count,
            "feature_rrna": rrna_count,
            "feature_ncrna": 15
        },
        "features": [
            {
                "type": "cds",
                "contig": "contig_1",
                "start": 190,
                "stop": 255,
                "strand": "+",
                "gene": "thrL",
                "product": "thr operon leader peptide"
            },
            {
                "type": "cds",
                "contig": "contig_1",
                "start": 337,
                "stop": 2799,
                "strand": "+",
                "gene": "thrA",
                "product": "Bifunctional aspartokinase/homoserine dehydrogenase 1"
            }
        ]
    }
    
    json_file = output_path / f"{prefix}.json"
    json_file.write_text(json.dumps(bakta_result, indent=2))
    
    # Criar GFF3
    gff3_content = """##gff-version 3
##feature-ontology http://song.cvs.sourceforge.net/viewvc/song/ontology/sofa.obo?revision=1.269
##Type DNA 4639675
contig_1	Bakta	region	1	4639675	.	+	.	ID=contig_1;Name=contig_1
contig_1	Prodigal	CDS	190	255	.	+	0	ID=thrL;Name=thrL;gene=thrL;product=thr operon leader peptide
contig_1	Prodigal	CDS	337	2799	.	+	0	ID=thrA;Name=thrA;gene=thrA;product=Bifunctional aspartokinase/homoserine dehydrogenase 1
"""
    gff3_file = output_path / f"{prefix}.gff3"
    gff3_file.write_text(gff3_content)
    
    # Criar FAA (proteínas)
    faa_content = ">thrL | thr operon leader peptide\nMKRISTTITTTITITTGNGAG\n>thrA | Bifunctional aspartokinase/homoserine dehydrogenase 1\nMKVLKDVARLAGVSTTTVSHVINKTRFRETLEHIVPVIDDNGVLYDTHFPTDPIEAVAK\n"
    faa_file = output_path / f"{prefix}.faa"
    faa_file.write_text(faa_content)
    
    # Criar FFN (features nucleotídicas)
    ffn_content = ">thrL | thr operon leader peptide\nATGAAACGCATTAGCACCACCATTACCACCACCATCACCATTACCACAGGTAACGGTGCGGGCTGA\n>thrA | Bifunctional aspartokinase/homoserine dehydrogenase 1\nGTGAAAAAGCTGACTGATGTGGATGAGTTTGATGTTGATGTTGATGTTGATGTTGATGTTGAT\n"
    ffn_file = output_path / f"{prefix}.ffn"
    ffn_file.write_text(ffn_content)
    
    # Criar resumo TXT
    summary = f"""Bakta Annotation Summary
========================
Genome: {prefix}
Date: {datetime.now().isoformat()}

Genome Statistics:
  Size: {genome_size:,} bp
  GC content: {gc_content:.2f}%
  Contigs: 1
  N50: {genome_size:,}

Feature Summary:
  CDS: {cds_count}
  Genes: {cds_count}
  tRNAs: {trna_count}
  rRNAs: {rrna_count}
  ncRNAs: 15

Files generated:
  - {prefix}.json
  - {prefix}.gff3
  - {prefix}.faa
  - {prefix}.ffn
  - {prefix}.txt
"""
    txt_file = output_path / f"{prefix}.txt"
    txt_file.write_text(summary)
    
    # Criar job_summary.json
    job_summary = {
        "job_id": Path(output_dir).name,
        "status": "completed",
        "prefix": prefix,
        "output_dir": str(output_dir),
        "files": {
            "json": {"path": str(json_file), "description": "Resultados JSON", "size": json_file.stat().st_size},
            "gff3": {"path": str(gff3_file), "description": "Anotação GFF3", "size": gff3_file.stat().st_size},
            "faa": {"path": str(faa_file), "description": "Proteínas traduzidas", "size": faa_file.stat().st_size},
            "ffn": {"path": str(ffn_file), "description": "Features nucleotídicas", "size": ffn_file.stat().st_size},
            "txt": {"path": str(txt_file), "description": "Resumo", "size": txt_file.stat().st_size}
        },
        "stats": {
            "genome_size": genome_size,
            "gc_content": gc_content,
            "n_contigs": 1,
            "n50": genome_size,
            "cds": cds_count,
            "genes": cds_count,
            "trnas": trna_count,
            "rrnas": rrna_count,
            "ncrnas": 15
        }
    }
    
    summary_file = output_path / "job_summary.json"
    summary_file.write_text(json.dumps(job_summary, indent=2))
    
    return job_summary


def main():
    """Função principal."""
    print("\n" + "="*60)
    print("  Bakta Flow Pipeline DEMO")
    print("  (Modo Simulacao - Sem Bakta instalado)")
    print("="*60)
    
    # Verificar templates
    templates_dir = Path("data/templates")
    if not templates_dir.exists():
        print("\n❌ Diretório de templates não encontrado!")
        print("   Execute primeiro: python data/download_templates.py --dummy")
        return 1
    
    templates = list(templates_dir.glob("*.fasta"))
    if not templates:
        print("\nNenhum template encontrado!")
        return 1
    
    # Mostrar templates disponíveis
    print_header("Templates Disponiveis")
    for i, template in enumerate(templates, 1):
        size = template.stat().st_size
        print(f"  {i}. {template.name:<30} ({size:,} bytes)")
    
    # Usar primeiro template
    selected_template = templates[0]
    print(f"\nUsando template: {selected_template.name}")
    
    # Configurar output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    job_id = f"{timestamp}_demo"
    output_dir = Path("resultados") / job_id
    prefix = selected_template.stem
    
    print(f"Diretorio de saida: {output_dir}")
    
    # Executar simulacao
    start_time = time.time()
    
    try:
        result = simulate_bakta_execution(
            input_file=selected_template,
            output_dir=output_dir,
            prefix=prefix,
            threads=4
        )
        
        elapsed = time.time() - start_time
        
        # Mostrar resultados
        print_header("ANOTACAO CONCLUIDA!")
        
        print(f"\nResumo:")
        print(f"   Job ID: {result['job_id']}")
        print(f"   Tempo: {elapsed:.2f} segundos")
        print(f"   Diretório: {result['output_dir']}")
        
        print(f"\nEstatisticas:")
        stats = result['stats']
        print(f"   Tamanho: {stats['genome_size']:,} bp")
        print(f"   GC: {stats['gc_content']:.2f}%")
        print(f"   CDS: {stats['cds']}")
        print(f"   tRNAs: {stats['trnas']}")
        print(f"   rRNAs: {stats['rrnas']}")
        
        print(f"\nArquivos Gerados:")
        for ext, info in result['files'].items():
            print(f"   [OK] {ext.upper():<6} - {info['description']:<25} ({info['size']:,} bytes)")
        
        print(f"\nProximos passos:")
        print(f"   1. Verifique os resultados em: {output_dir}")
        print(f"   2. Inicie o servidor: cd backend && python app.py")
        print(f"   3. Acesse: http://localhost:5000")
        
        print("\n" + "="*60)
        
        return 0
        
    except Exception as e:
        print(f"\nERRO durante demonstracao: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
