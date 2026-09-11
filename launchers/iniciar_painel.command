#!/bin/bash
cd "$(dirname "$0")/.."
if [ ! -d ".venv" ]; then
    echo "Ambiente ainda não configurado. Rode configurar_ambiente.command primeiro."
    read -p "Pressione Enter para sair..."
    exit 1
fi
source .venv/bin/activate
streamlit run app.py
