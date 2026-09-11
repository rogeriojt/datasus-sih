# -*- coding: utf-8 -*-
import pandas as pd
import pytest

from datasus.catalogo import importar_xlsx
from datasus.db import conexao


def test_importar_xlsx_grava_procedimentos_ativos(tmp_path):
    caminho = tmp_path / "procedimentos.xlsx"
    df = pd.DataFrame([
        {"Codigo_SIGTAP": "505020092", "Descricao_SIGTAP": "TX Rim", "Grupo_Proc": "G",
         "Subgrupo_Proc": "S", "Categoria": "TX Rim", "Tipo_TX_CC": "Transplante", "Ativo": "Sim"},
        {"Codigo_SIGTAP": "111111111", "Descricao_SIGTAP": "Inativo", "Grupo_Proc": "G",
         "Subgrupo_Proc": "S", "Categoria": "X", "Tipo_TX_CC": "CC", "Ativo": "Não"},
    ])
    with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Procedimentos")

    ativos = importar_xlsx(caminho)
    assert ativos == 1

    with conexao() as conn:
        linhas = conn.execute("SELECT codigo_sigtap, ativo FROM procedimentos").fetchall()
    codigos = {r["codigo_sigtap"]: r["ativo"] for r in linhas}
    assert codigos["0505020092"] == 1
    assert codigos["0111111111"] == 0


def test_importar_xlsx_arquivo_inexistente(tmp_path):
    with pytest.raises(FileNotFoundError):
        importar_xlsx(tmp_path / "nao_existe.xlsx")
