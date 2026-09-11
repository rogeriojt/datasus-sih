# -*- coding: utf-8 -*-
from datasus.db import conexao, inicializar_banco, transacao


def test_inicializar_banco_e_idempotente():
    inicializar_banco()
    inicializar_banco()
    with conexao() as conn:
        tabelas = {
            r["name"] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    esperado = {"procedimentos", "competencias", "procedimentos_realizados",
                "estabelecimentos", "municipios"}
    assert esperado.issubset(tabelas)


def test_transacao_reverte_em_caso_de_erro():
    try:
        with transacao() as conn:
            conn.execute(
                "INSERT INTO procedimentos (codigo_sigtap, ativo) VALUES ('X', 1)"
            )
            raise ValueError("erro proposital")
    except ValueError:
        pass

    with conexao() as conn:
        n = conn.execute("SELECT COUNT(*) AS n FROM procedimentos").fetchone()["n"]
    assert n == 0


def test_upsert_de_competencia_atualiza_em_vez_de_duplicar():
    with transacao() as conn:
        conn.execute(
            "INSERT INTO competencias (uf, ano, mes, status, tentativas, atualizado_em) "
            "VALUES ('CE', 2025, 1, 'falha', 1, 'x') "
            "ON CONFLICT(uf, ano, mes) DO UPDATE SET status=excluded.status"
        )
        conn.execute(
            "INSERT INTO competencias (uf, ano, mes, status, tentativas, atualizado_em) "
            "VALUES ('CE', 2025, 1, 'sucesso', 1, 'y') "
            "ON CONFLICT(uf, ano, mes) DO UPDATE SET status=excluded.status"
        )
    with conexao() as conn:
        linhas = conn.execute("SELECT status FROM competencias WHERE uf='CE'").fetchall()
    assert len(linhas) == 1
    assert linhas[0]["status"] == "sucesso"
