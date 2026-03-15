#!/usr/bin/env python3
"""
Bakta Flow Setup Script
Script de configuração automática do ambiente
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def print_header(text):
    """Printa header formatado."""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)


def check_conda():
    """Verifica se Conda está instalado."""
    try:
        result = subprocess.run(
            ["conda", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✅ Conda encontrado: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Conda não encontrado!")
        print("   Por favor, instale o Miniconda:")
        print("   https://docs.conda.io/en/latest/miniconda.html")
        return False


def create_environment():
    """Cria o ambiente Conda."""
    print_header("Criando Ambiente Conda")
    
    env_file = Path("environment.yml")
    if not env_file.exists():
        print(f"❌ Arquivo {env_file} não encontrado!")
        return False
    
    try:
        print("📦 Criando ambiente 'bakta_env'...")
        print("   Isso pode levar alguns minutos...")
        
        subprocess.run(
            ["conda", "env", "create", "-f", "environment.yml"],
            check=True
        )
        
        print("✅ Ambiente criado com sucesso!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao criar ambiente: {e}")
        return False


def download_database(db_type="light"):
    """Baixa a base de dados do Bakta."""
    print_header(f"Baixando Database Bakta ({db_type})")
    
    db_path = Path(f"bakta-{db_type}")
    
    if db_path.exists() and any(db_path.iterdir()):
        print(f"⚠️  Database já existe em: {db_path.absolute()}")
        response = input("   Deseja reinstalar? (s/N): ")
        if response.lower() != 's':
            print("   Pulando download...")
            return True
    
    try:
        print(f"📥 Baixando database {db_type}...")
        print("   Isso pode levar vários minutos dependendo da conexão...")
        
        # Ativar ambiente e baixar
        cmd = f"""
        conda activate bakta_env && 
        bakta_db download --type {db_type} --output {db_path}
        """
        
        subprocess.run(cmd, shell=True, check=True)
        
        print(f"✅ Database instalado em: {db_path.absolute()}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao baixar database: {e}")
        print("   Você pode tentar manualmente mais tarde com:")
        print(f"   bakta_db download --type {db_type} --output ./bakta-{db_type}")
        return False


def setup_directories():
    """Cria estrutura de diretórios."""
    print_header("Configurando Diretórios")
    
    dirs = [
        "resultados",
        "data/uploads",
        "data/templates",
        "logs"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"  📁 {dir_path}/")
    
    print("✅ Diretórios criados!")


def download_templates():
    """Baixa templates de genomas."""
    print_header("Baixando Templates de Genomas")
    
    script = Path("data/download_templates.py")
    if not script.exists():
        print(f"❌ Script {script} não encontrado!")
        return False
    
    try:
        print("🧬 Criando templates (modo dummy)...")
        
        subprocess.run(
            [sys.executable, str(script), "--output", "data/templates", "--dummy"],
            check=True
        )
        
        print("✅ Templates criados!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Erro ao criar templates: {e}")
        return False


def test_installation():
    """Testa a instalação."""
    print_header("Testando Instalação")
    
    try:
        # Testar Bakta
        result = subprocess.run(
            "conda activate bakta_env && bakta --version",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ Bakta: {result.stdout.strip()}")
        else:
            print("⚠️  Bakta não encontrado no PATH")
        
        # Testar Python imports
        test_script = """
import sys
sys.path.insert(0, 'backend')
from pipeline import BaktaPipeline
print("✅ Pipeline importado com sucesso")
        """
        
        result = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(result.stdout.strip())
        else:
            print("⚠️  Erro ao importar pipeline")
            print(result.stderr)
        
        return True
        
    except Exception as e:
        print(f"⚠️  Erro no teste: {e}")
        return False


def print_final_message():
    """Printa mensagem final."""
    print("\n" + "="*60)
    print("  🎉 SETUP CONCLUÍDO!")
    print("="*60)
    print("\nPróximos passos:")
    print("\n1. Ative o ambiente:")
    print("   conda activate bakta_env")
    print("\n2. Inicie o servidor:")
    print("   cd backend && python app.py")
    print("\n3. Acesse no navegador:")
    print("   http://localhost:5000")
    print("\n4. Ou use Docker:")
    print("   cd deployment && docker-compose up")
    print("\n" + "="*60)


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description="Setup do Bakta Flow"
    )
    parser.add_argument(
        "--skip-conda",
        action="store_true",
        help="Pula verificação do Conda"
    )
    parser.add_argument(
        "--db-type",
        default="light",
        choices=["light", "full"],
        help="Tipo de database (light ou full)"
    )
    parser.add_argument(
        "--skip-db",
        action="store_true",
        help="Pula download do database"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("  🧬 Bakta Flow Setup")
    print("="*60)
    
    # Verificar Conda
    if not args.skip_conda:
        if not check_conda():
            print("\n❌ Conda é necessário para continuar!")
            print("   Instale em: https://docs.conda.io/en/latest/miniconda.html")
            return 1
    
    # Criar ambiente
    if not create_environment():
        print("\n⚠️  Continuando mesmo com erro na criação do ambiente...")
    
    # Setup diretórios
    setup_directories()
    
    # Download database
    if not args.skip_db:
        download_database(args.db_type)
    
    # Download templates
    download_templates()
    
    # Testar instalação
    test_installation()
    
    # Mensagem final
    print_final_message()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
