#!/bin/bash
cd "$(dirname "$0")/.."
if [ ! -d ".venv" ]; then
    echo "Ambiente ainda não configurado. Rode configurar_ambiente.command primeiro."
    read -p "Pressione Enter para sair..."
    exit 1
fi
source .venv/bin/activate
echo "--- Coletando competências pendentes ---"
python cli.py coletar
echo ""
echo "--- Retentando falhas / suspeitas de falha silenciosa ---"
python cli.py retentar-falhas
echo ""
echo "--- Atualizando nomes de estabelecimentos ---"
python cli.py corrigir-nomes
echo ""
echo "--- Verificando integridade ---"
python cli.py integridade
echo ""
read -p "Pressione Enter para sair..."
