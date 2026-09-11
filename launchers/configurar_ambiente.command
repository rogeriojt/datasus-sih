#!/bin/bash
# Prepara o ambiente local (uma vez só): cria o .venv e instala as
# dependências. Rode isto primeiro, antes de usar os outros launchers.
cd "$(dirname "$0")/.."
echo "============================================================"
echo "  Configurando ambiente local do DATASUS SIH"
echo "============================================================"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
python cli.py importar-procedimentos
echo ""
echo "Pronto! Use iniciar_painel.command para abrir o painel, ou"
echo "atualizar_dados.command para rodar a coleta manualmente."
read -p "Pressione Enter para sair..."
