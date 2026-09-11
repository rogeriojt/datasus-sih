# -*- coding: utf-8 -*-
"""Testes da função pura `organizar` (sem rede, sem banco)."""
import pandas as pd

from datasus.coleta import organizar


def _bruto(linhas):
    return pd.DataFrame(linhas)


def test_filtra_apenas_codigos_monitorados():
    bruto = _bruto([
        {"PROC_REA": "0505020092", "N_AIH": "1", "CNES": "123"},
        {"PROC_REA": "9999999999", "N_AIH": "2", "CNES": "456"},
    ])
    resultado = organizar(bruto, {"0505020092"}, "CE", 2025, 1)
    assert len(resultado) == 1
    assert resultado.iloc[0]["codigo_sigtap"] == "0505020092"


def test_ano_mes_sao_os_de_competencia():
    bruto = _bruto([{"PROC_REA": "0505020092", "N_AIH": "1", "CNES": "123"}])
    resultado = organizar(bruto, {"0505020092"}, "CE", 2025, 6)
    linha = resultado.iloc[0]
    assert (linha["ano"], linha["mes"]) == (2025, 6)


def test_dataframe_vazio_sem_proc_rea():
    bruto = _bruto([{"OUTRA_COLUNA": 1}])
    resultado = organizar(bruto, {"0505020092"}, "CE", 2025, 1)
    assert resultado.empty


def test_dataframe_bruto_none():
    resultado = organizar(None, {"0505020092"}, "CE", 2025, 1)
    assert resultado.empty


def test_normaliza_cnes_e_codigo_sigtap():
    bruto = _bruto([{"PROC_REA": 505020092.0, "N_AIH": "1", "CNES": 2078}])
    resultado = organizar(bruto, {"0505020092"}, "CE", 2025, 1)
    assert resultado.iloc[0]["codigo_sigtap"] == "0505020092"
    assert resultado.iloc[0]["cnes"] == "0002078"


def test_extrai_municipio_de_munic_mov():
    bruto = _bruto([
        {"PROC_REA": "0505020092", "N_AIH": "1", "CNES": "123", "MUNIC_MOV": "230440"},
    ])
    resultado = organizar(bruto, {"0505020092"}, "CE", 2025, 1)
    assert resultado.iloc[0]["municipio_codigo"] == "230440"
