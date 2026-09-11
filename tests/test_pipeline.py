# -*- coding: utf-8 -*-
"""Testes de ponta a ponta do pipeline de coleta, com o download real
(`datasus.download.baixar_competencia`) substituído por um dublê —
nenhum destes testes toca a rede."""
import pandas as pd

from datasus import coleta
from datasus.download import ResultadoDownload
from datasus.db import conexao, transacao


def _cadastrar_procedimento(codigo="0505020092"):
    with transacao() as conn:
        conn.execute(
            "INSERT INTO procedimentos (codigo_sigtap, descricao, categoria, tipo, ativo) "
            "VALUES (?,?,?,?,1)",
            (codigo, "Transplante de Rim", "TX Rim", "Transplante"),
        )
    return {codigo}


def test_competencia_com_sucesso_e_persistida(monkeypatch):
    codigos = _cadastrar_procedimento()

    def fake_download(uf, ano, mes):
        bruto = pd.DataFrame([
            {"PROC_REA": "0505020092", "N_AIH": "1", "CNES": "123"},
            {"PROC_REA": "0505020092", "N_AIH": "2", "CNES": "456"},
        ])
        return ResultadoDownload(bruto=bruto, total_bruto=len(bruto))

    monkeypatch.setattr(coleta, "baixar_competencia", fake_download)

    _, _, _, status, _ = coleta.processar_competencia("CE", 2025, 1, codigos)
    assert status == "sucesso"

    with conexao() as conn:
        n = conn.execute("SELECT COUNT(*) AS n FROM procedimentos_realizados").fetchone()["n"]
        c = conn.execute("SELECT status, total_bruto, total_filtrado FROM competencias").fetchone()
    assert n == 2
    assert c["status"] == "sucesso"
    assert c["total_bruto"] == 2
    assert c["total_filtrado"] == 2


def test_download_bruto_vazio_marca_suspeita(monkeypatch):
    codigos = _cadastrar_procedimento()

    def fake_download(uf, ano, mes):
        return ResultadoDownload(bruto=pd.DataFrame(), total_bruto=0)

    monkeypatch.setattr(coleta, "baixar_competencia", fake_download)
    _, _, _, status, _ = coleta.processar_competencia("CE", 2025, 1, codigos)
    assert status == "suspeita_falha_silenciosa"


def test_bruto_nao_vazio_mas_sem_procedimento_monitorado_e_sucesso_de_verdade(monkeypatch):
    codigos = _cadastrar_procedimento()

    def fake_download(uf, ano, mes):
        bruto = pd.DataFrame([{"PROC_REA": "9999999999", "N_AIH": "1", "CNES": "1"}])
        return ResultadoDownload(bruto=bruto, total_bruto=len(bruto))

    monkeypatch.setattr(coleta, "baixar_competencia", fake_download)
    _, _, _, status, _ = coleta.processar_competencia("CE", 2025, 1, codigos)
    assert status == "sucesso"


def test_falha_persistente_marca_status_falha(monkeypatch):
    codigos = _cadastrar_procedimento()

    def fake_download(uf, ano, mes):
        raise RuntimeError("timeout simulado")

    monkeypatch.setattr(coleta, "baixar_competencia", fake_download)
    monkeypatch.setattr(coleta.settings, "PAUSA_ENTRE_TENTATIVAS_SEG", 0)

    _, _, _, status, msg = coleta.processar_competencia("CE", 2025, 1, codigos)
    assert status == "falha"
    assert "timeout simulado" in msg


def test_reprocessar_competencia_e_idempotente(monkeypatch):
    codigos = _cadastrar_procedimento()
    chamadas = {"n": 0}

    def fake_download(uf, ano, mes):
        chamadas["n"] += 1
        bruto = pd.DataFrame([{"PROC_REA": "0505020092", "N_AIH": f"{chamadas['n']}-A", "CNES": "1"}])
        return ResultadoDownload(bruto=bruto, total_bruto=len(bruto))

    monkeypatch.setattr(coleta, "baixar_competencia", fake_download)
    coleta.processar_competencia("CE", 2025, 1, codigos)
    coleta.processar_competencia("CE", 2025, 1, codigos)

    with conexao() as conn:
        n = conn.execute(
            "SELECT COUNT(*) AS n FROM procedimentos_realizados WHERE uf='CE' AND ano=2025 AND mes=1"
        ).fetchone()["n"]
    assert n == 1


def test_retentar_falhas_reprocessa_suspeitas(monkeypatch):
    codigos = _cadastrar_procedimento()
    respostas = iter([ResultadoDownload(bruto=pd.DataFrame(), total_bruto=0)])

    def fake_download_inicial(uf, ano, mes):
        return next(respostas)

    monkeypatch.setattr(coleta, "baixar_competencia", fake_download_inicial)
    coleta.processar_competencia("CE", 2025, 1, codigos)

    with conexao() as conn:
        status_antes = conn.execute("SELECT status FROM competencias").fetchone()["status"]
    assert status_antes == "suspeita_falha_silenciosa"

    def fake_download_retry(uf, ano, mes):
        bruto = pd.DataFrame([{"PROC_REA": "0505020092", "N_AIH": "1", "CNES": "1"}])
        return ResultadoDownload(bruto=bruto, total_bruto=len(bruto))

    monkeypatch.setattr(coleta, "baixar_competencia", fake_download_retry)
    coleta.retentar_falhas()

    with conexao() as conn:
        status_depois = conn.execute("SELECT status FROM competencias").fetchone()["status"]
    assert status_depois == "sucesso"


def test_competencias_do_periodo_nao_inclui_futuro():
    resultado = coleta.competencias_do_periodo(["CE"], [2099], [1])
    assert resultado == []


def test_competencias_do_periodo_gera_pares_esperados():
    resultado = coleta.competencias_do_periodo(["CE", "SP"], [2020], [1, 2])
    assert set(resultado) == {("CE", 2020, 1), ("CE", 2020, 2), ("SP", 2020, 1), ("SP", 2020, 2)}
