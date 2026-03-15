#!/bin/bash
# PUC Minas - Bakta Entrypoint Script
# Script de inicialização do container Bakta

set -e

echo "========================================"
echo "  PUC Minas - Bakta Container"
echo "========================================"

# Ativar ambiente conda
source /opt/conda/etc/profile.d/conda.sh
conda activate bakta_env

echo ""
echo "🔧 Verificando instalação..."

# Verificar Bakta
if command -v bakta &> /dev/null; then
    BAKTA_VERSION=$(bakta --version 2>&1 | head -1)
    echo "✅ Bakta: $BAKTA_VERSION"
else
    echo "❌ Bakta não encontrado!"
    exit 1
fi

# Verificar/Instalar database
DB_PATH="${BAKTA_DB:-/app/bakta-light}"
DB_READY_MARKER="$DB_PATH/.db-ready"
DB_LOCK_FILE="$DB_PATH/.db-downloading"

echo ""
echo "📦 Verificando database em: $DB_PATH"

mkdir -p "$DB_PATH"

if [ -f "$DB_READY_MARKER" ]; then
    echo "✅ Database marcado como pronto"
else
    echo "⚠️  Database ainda não pronto. O frontend/API subirá agora e o download seguirá em background."
    echo "   (Anotações podem falhar até a conclusão do download.)"

    if [ -f "$DB_LOCK_FILE" ] && ! pgrep -f "bakta_db download" >/dev/null 2>&1; then
        echo "⚠️  Lock de download encontrado sem processo ativo. Reiniciando download..."
        rm -f "$DB_LOCK_FILE"
    fi

    if [ ! -f "$DB_LOCK_FILE" ]; then
        touch "$DB_LOCK_FILE"
        (
            echo "📥 Iniciando download do database light em background..."
            if bakta_db download --type light --output "$DB_PATH"; then
                touch "$DB_READY_MARKER"
                echo "✅ Database instalado com sucesso!"
            else
                echo "❌ Falha no download do database Bakta"
            fi
            rm -f "$DB_LOCK_FILE"
        ) &
    else
        echo "ℹ️  Download do database já está em andamento"
    fi
fi

# Verificar estrutura de diretórios
echo ""
echo "📁 Verificando diretórios..."
mkdir -p /app/data/uploads /app/data/templates /app/resultados
ls -la /app/data /app/resultados

# Verificar Python/Flask
echo ""
echo "🐍 Verificando Python..."
python --version
pip show flask flask-cors | grep -E "^(Name|Version):"

echo ""
echo "========================================"
echo "  Iniciando servidor web..."
echo "========================================"
echo ""
echo "🌐 Acesse: http://localhost:5000"
echo "📊 API: http://localhost:5000/api/status"
echo ""
echo "Pressione Ctrl+C para parar"
echo ""

# Iniciar aplicação Flask
export PYTHONPATH=/app
cd /app/backend
exec python app.py
