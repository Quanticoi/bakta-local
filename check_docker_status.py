#!/usr/bin/env python3
"""
Script para verificar status do Docker do Bakta
"""

import subprocess
import sys
import time

def run_command(cmd):
    """Executa comando e retorna output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def check_status():
    print("="*60)
    print("  Bakta Flow - Status do Docker")
    print("="*60)
    print()
    
    # Verificar containers
    print("Containers:")
    stdout, stderr, rc = run_command("docker ps -a --filter name=bakta")
    if "bakta" in stdout.lower():
        print(stdout)
    else:
        print("  Nenhum container do Bakta encontrado")
    print()
    
    # Verificar imagens
    print("Imagens:")
    stdout, stderr, rc = run_command("docker images")
    if "pucminas" in stdout.lower() or "bakta" in stdout.lower():
        # Filtrar apenas linhas relevantes
        lines = stdout.split('\n')
        for line in lines:
            if 'pucminas' in line.lower() or 'bakta' in line.lower() or 'REPOSITORY' in line:
                print(f"  {line}")
    else:
        print("  Imagem ainda nao construida")
    print()
    
    # Verificar volumes
    print("Volumes:")
    stdout, stderr, rc = run_command("docker volume ls")
    if "bakta" in stdout.lower():
        print(stdout)
    else:
        print("  Volume padrao sendo usado")
    print()
    
    # Verificar se porta 5000 está em uso
    print("Porta 5000:")
    stdout, stderr, rc = run_command("docker ps --format 'table {{.Names}}\t{{.Ports}}' | findstr 5000")
    if stdout:
        print(f"  {stdout}")
    else:
        print("  Porta 5000 nao esta em uso por nenhum container")
    print()
    
    print("="*60)
    print("Para iniciar o container, execute:")
    print("  cd deployment && docker-compose up --build -d")
    print()
    print("Para ver logs em tempo real:")
    print("  docker logs -f puc-bakta")
    print("="*60)

if __name__ == "__main__":
    check_status()
