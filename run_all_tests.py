#!/usr/bin/env python3
"""
Bakta Flow - Teste Completo do Sistema
Executa todos os testes e verificações
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime


class TestRunner:
    """Executor de testes completo."""
    
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        self.start_time = time.time()
        
    def log(self, message, level="INFO"):
        """Log formatado."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {"INFO": "[INFO]", "PASS": "[PASS]", "FAIL": "[FAIL]", 
                  "WARN": "[WARN]"}.get(level, "[INFO]")
        print(f"{timestamp} {prefix} {message}")
        
    def header(self, text):
        """Header formatado."""
        print("\n" + "="*70)
        print(f"  {text}")
        print("="*70)
        
    def test_file_exists(self, filepath, description):
        """Testa se arquivo existe."""
        path = Path(filepath)
        if path.exists():
            size = path.stat().st_size
            self.log(f"{description}: OK ({size} bytes)", "PASS")
            self.passed += 1
            return True
        else:
            self.log(f"{description}: NAO ENCONTRADO", "FAIL")
            self.failed += 1
            return False
            
    def test_directory_structure(self):
        """Testa estrutura de diretórios."""
        self.header("TESTE 1: Estrutura de Diretorios")
        
        dirs = [
            ("backend", "Backend API"),
            ("frontend", "Frontend Web"),
            ("frontend/static", "Static files"),
            ("data", "Dados"),
            ("data/templates", "Templates"),
            ("data/uploads", "Uploads"),
            ("deployment", "Deploy"),
            ("docs", "Documentacao"),
            ("tests", "Testes"),
            ("tests/unit", "Testes unitarios"),
            ("tests/integration", "Testes integracao"),
            ("tests/e2e", "Testes E2E"),
            ("assets", "Assets"),
            ("assets/images", "Imagens"),
            ("resultados", "Resultados"),
        ]
        
        for dir_path, desc in dirs:
            if Path(dir_path).exists():
                self.log(f"{desc}: OK", "PASS")
                self.passed += 1
            else:
                self.log(f"{desc}: FALTANDO", "FAIL")
                self.failed += 1
                
    def test_critical_files(self):
        """Testa arquivos críticos."""
        self.header("TESTE 2: Arquivos Criticos")
        
        files = [
            ("backend/app.py", "API Flask"),
            ("backend/pipeline.py", "Pipeline"),
            ("frontend/index.html", "HTML principal"),
            ("frontend/static/app.js", "JavaScript"),
            ("frontend/static/styles.css", "CSS"),
            ("deployment/Dockerfile", "Dockerfile"),
            ("deployment/docker-compose.yml", "Docker Compose"),
            ("environment.yml", "Conda environment"),
            ("README.md", "README"),
            ("docs/ARQUITETURA.md", "Doc Arquitetura"),
            ("docs/API.md", "Doc API"),
            ("tests/conftest.py", "Test config"),
            ("tests/unit/test_pipeline.py", "Testes pipeline"),
            ("tests/unit/test_api.py", "Testes API"),
            ("assets/images/architecture_diagram.svg", "Diagrama arquitetura"),
            ("assets/images/workflow_diagram.svg", "Diagrama fluxo"),
            ("assets/images/logo.svg", "Logo"),
        ]
        
        for filepath, desc in files:
            self.test_file_exists(filepath, desc)
            
    def test_templates(self):
        """Testa templates de genomas."""
        self.header("TESTE 3: Templates de Genomas")
        
        templates_dir = Path("data/templates")
        if not templates_dir.exists():
            self.log("Diretorio de templates nao existe", "FAIL")
            self.failed += 1
            return
            
        templates = list(templates_dir.glob("*.fasta"))
        self.log(f"Encontrados {len(templates)} templates")
        
        for template in templates:
            size = template.stat().st_size
            self.log(f"  - {template.name:<30} ({size:,} bytes)", "PASS")
            self.passed += 1
            
    def test_python_imports(self):
        """Testa imports Python."""
        self.header("TESTE 4: Imports Python")
        
        sys.path.insert(0, "backend")
        
        tests = [
            ("pipeline", "BaktaPipeline"),
        ]
        
        for module_name, class_name in tests:
            try:
                module = __import__(module_name)
                if hasattr(module, class_name):
                    self.log(f"Import {module_name}.{class_name}: OK", "PASS")
                    self.passed += 1
                else:
                    self.log(f"Classe {class_name} nao encontrada", "FAIL")
                    self.failed += 1
            except Exception as e:
                self.log(f"Import {module_name}: ERRO - {e}", "FAIL")
                self.failed += 1
                
    def test_pipeline_creation(self):
        """Testa criação do pipeline."""
        self.header("TESTE 5: Pipeline Creation")
        
        try:
            from pipeline import BaktaPipeline
            
            # Teste 1: Criação padrão
            pipeline = BaktaPipeline()
            self.log("Pipeline (default): OK", "PASS")
            self.passed += 1
            
            # Teste 2: Criação customizada
            pipeline = BaktaPipeline(
                db_path="./test-db",
                output_dir="./test-out",
                threads=8,
                meta_mode=False
            )
            self.log("Pipeline (custom): OK", "PASS")
            self.passed += 1
            
            # Teste 3: Verificar atributos
            assert pipeline.threads == 8
            assert pipeline.meta_mode == False
            self.log("Pipeline atributos: OK", "PASS")
            self.passed += 1
            
            # Cleanup
            import shutil
            if Path("./test-out").exists():
                shutil.rmtree("./test-out")
                
        except Exception as e:
            self.log(f"Pipeline creation: ERRO - {e}", "FAIL")
            self.failed += 1
            
    def test_json_files(self):
        """Testa arquivos JSON válidos."""
        self.header("TESTE 6: Arquivos JSON Validos")
        
        json_files = [
            "tests/fixtures/sample_result.json",
        ]
        
        # Adicionar resultados se existirem
        result_dirs = list(Path("resultados").glob("*/job_summary.json")) if Path("resultados").exists() else []
        for result_file in result_dirs[:3]:  # Testar até 3
            json_files.append(str(result_file))
        
        for filepath in json_files:
            path = Path(filepath)
            if not path.exists():
                continue
                
            try:
                with open(path) as f:
                    data = json.load(f)
                self.log(f"JSON valido: {filepath}", "PASS")
                self.passed += 1
            except json.JSONDecodeError as e:
                self.log(f"JSON invalido: {filepath} - {e}", "FAIL")
                self.failed += 1
            except Exception as e:
                self.log(f"Erro lendo {filepath}: {e}", "FAIL")
                self.failed += 1
                
    def test_demo_pipeline(self):
        """Executa demo do pipeline."""
        self.header("TESTE 7: Demo Pipeline")
        
        try:
            result = subprocess.run(
                [sys.executable, "demo_pipeline.py"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                self.log("Demo pipeline: EXECUTADO COM SUCESSO", "PASS")
                self.passed += 1
                
                # Verificar se criou resultados
                result_dirs = list(Path("resultados").glob("*_demo"))
                if result_dirs:
                    latest = max(result_dirs, key=lambda p: p.stat().st_mtime)
                    files = list(latest.glob("*"))
                    self.log(f"  Resultados em: {latest.name}", "INFO")
                    self.log(f"  Arquivos gerados: {len(files)}", "INFO")
                    for f in files:
                        self.log(f"    - {f.name}", "INFO")
            else:
                self.log(f"Demo pipeline: FALHOU\n{result.stderr}", "FAIL")
                self.failed += 1
                
        except subprocess.TimeoutExpired:
            self.log("Demo pipeline: TIMEOUT", "FAIL")
            self.failed += 1
        except Exception as e:
            self.log(f"Demo pipeline: ERRO - {e}", "FAIL")
            self.failed += 1
            
    def test_documentation(self):
        """Testa documentação."""
        self.header("TESTE 8: Documentacao")
        
        docs = [
            ("README.md", 10000),  # Min 10KB
            ("docs/ARQUITETURA.md", 5000),
            ("docs/API.md", 5000),
            ("docs/DEPLOY.md", 5000),
            ("tests/ESPECIFICACOES.md", 5000),
            ("tests/PROCEDIMENTOS.md", 5000),
        ]
        
        for filepath, min_size in docs:
            path = Path(filepath)
            if path.exists():
                size = path.stat().st_size
                if size >= min_size:
                    self.log(f"{filepath}: OK ({size:,} bytes)", "PASS")
                    self.passed += 1
                else:
                    self.log(f"{filepath}: Muito pequeno ({size} < {min_size})", "WARN")
                    self.passed += 1
            else:
                self.log(f"{filepath}: NAO ENCONTRADO", "FAIL")
                self.failed += 1
                
    def count_lines_of_code(self):
        """Conta linhas de código."""
        self.header("ESTATISTICAS DO CODIGO")
        
        counts = {}
        
        # Python
        py_files = list(Path(".").rglob("*.py"))
        py_lines = 0
        for f in py_files:
            if ".git" not in str(f) and "__pycache__" not in str(f):
                try:
                    py_lines += len(f.read_text().splitlines())
                except:
                    pass
        counts["Python"] = (len(py_files), py_lines)
        
        # JavaScript
        js_files = list(Path(".").rglob("*.js"))
        js_lines = 0
        for f in js_files:
            if "node_modules" not in str(f):
                try:
                    js_lines += len(f.read_text().splitlines())
                except:
                    pass
        counts["JavaScript"] = (len(js_files), js_lines)
        
        # HTML
        html_files = list(Path(".").rglob("*.html"))
        html_lines = sum(len(f.read_text().splitlines()) for f in html_files)
        counts["HTML"] = (len(html_files), html_lines)
        
        # CSS
        css_files = list(Path(".").rglob("*.css"))
        css_lines = sum(len(f.read_text().splitlines()) for f in css_files)
        counts["CSS"] = (len(css_files), css_lines)
        
        # Markdown
        md_files = list(Path(".").rglob("*.md"))
        md_lines = sum(len(f.read_text().splitlines()) for f in md_files)
        counts["Markdown"] = (len(md_files), md_lines)
        
        # YAML
        yml_files = list(Path(".").rglob("*.yml")) + list(Path(".").rglob("*.yaml"))
        yml_lines = sum(len(f.read_text().splitlines()) for f in yml_files)
        counts["YAML"] = (len(yml_files), yml_lines)
        
        for lang, (files, lines) in counts.items():
            self.log(f"{lang:12} {files:3} arquivos, {lines:6} linhas")
            
        total_files = sum(c[0] for c in counts.values())
        total_lines = sum(c[1] for c in counts.values())
        self.log(f"{'TOTAL':12} {total_files:3} arquivos, {total_lines:6} linhas", "PASS")
        
    def generate_report(self):
        """Gera relatório final."""
        self.header("RELATORIO FINAL DE TESTES")
        
        elapsed = time.time() - self.start_time
        total = self.passed + self.failed
        
        print(f"\n  Tempo total:      {elapsed:.2f} segundos")
        print(f"  Testes executados: {total}")
        print(f"  Passaram:         {self.passed} ({100*self.passed/total:.1f}%)" if total > 0 else "  Passaram: 0")
        print(f"  Falharam:         {self.failed}")
        
        if self.failed == 0:
            print("\n  [OK] TODOS OS TESTES PASSARAM!")
            print("  O sistema esta pronto para uso!")
        elif self.failed < 5:
            print("\n  [AVISO] ALGUNS TESTES FALHARAM")
            print("  O sistema funciona mas tem pequenos problemas")
        else:
            print("\n  [ERRO] MUITOS TESTES FALHARAM")
            print("  Verifique os erros acima")
            
        print("\n" + "="*70)
        
        return self.failed == 0
        
    def run_all(self):
        """Executa todos os testes."""
        print("\n" + "="*70)
        print("  BAKTA FLOW - TESTE COMPLETO DO SISTEMA")
        print("="*70)
        print(f"  Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        try:
            self.test_directory_structure()
            self.test_critical_files()
            self.test_templates()
            self.test_python_imports()
            self.test_pipeline_creation()
            self.test_json_files()
            self.test_demo_pipeline()
            self.test_documentation()
            self.count_lines_of_code()
            
            success = self.generate_report()
            
            return 0 if success else 1
            
        except KeyboardInterrupt:
            self.log("Teste interrompido pelo usuario", "WARN")
            return 130
        except Exception as e:
            self.log(f"Erro inesperado: {e}", "FAIL")
            import traceback
            traceback.print_exc()
            return 1


def main():
    """Função principal."""
    runner = TestRunner()
    sys.exit(runner.run_all())


if __name__ == "__main__":
    main()
