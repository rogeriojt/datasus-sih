# -*- coding: utf-8 -*-
"""Cache de Razão Social e Nome Fantasia dos estabelecimentos CNES."""
from __future__ import annotations

import time
from datetime import datetime, timezone

import requests

from datasus.codigos import normalizar_codigo
from datasus.db import conexao, transacao

API_BASE = "https://apidadosabertos.saude.gov.br/cnes/estabelecimentos"
TIMEOUT = 60
PAUSA_ENTRE_CONSULTAS = 0.15
TAMANHO_PAGINA = 100


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _itens(dados) -> list[dict]:
    if isinstance(dados, dict):
        dados = dados.get("estabelecimentos", [])
    return [item for item in dados if isinstance(item, dict)] if isinstance(dados, list) else []


def _buscar_por_municipio(codigo_municipio: str) -> dict[str, tuple[str | None, str | None]]:
    """Consulta por município e indexa cada resultado pelo CNES exato."""
    encontrados: dict[str, tuple[str | None, str | None]] = {}
    offset = 0
    while True:
        resposta = requests.get(
            API_BASE,
            params={
                "codigo_municipio": int(codigo_municipio),
                "limit": TAMANHO_PAGINA,
                "offset": offset,
            },
            timeout=TIMEOUT,
        )
        resposta.raise_for_status()
        itens = _itens(resposta.json())
        if not itens:
            break
        for item in itens:
            codigo = normalizar_codigo(item.get("codigo_cnes"), 7)
            if not codigo:
                continue
            razao = str(item.get("nome_razao_social") or "").strip() or None
            fantasia = str(item.get("nome_fantasia") or "").strip() or None
            encontrados[codigo] = (razao, fantasia)
        if len(itens) < TAMANHO_PAGINA:
            break
        offset += TAMANHO_PAGINA
    return encontrados


def codigos_sem_nome() -> list[str]:
    with conexao() as conn:
        linhas = conn.execute(
            "SELECT DISTINCT pr.cnes FROM procedimentos_realizados pr "
            "LEFT JOIN estabelecimentos e ON e.cnes=pr.cnes "
            "WHERE pr.cnes IS NOT NULL AND pr.cnes<>'' "
            "AND (e.cnes IS NULL OR (e.razao_social IS NULL AND e.nome_fantasia IS NULL))"
        ).fetchall()
    return sorted(r["cnes"] for r in linhas)


def _municipios_por_cnes(codigos: list[str]) -> dict[str, str]:
    mapa: dict[str, str] = {}
    with conexao() as conn:
        for inicio in range(0, len(codigos), 500):
            lote = codigos[inicio:inicio + 500]
            if not lote:
                continue
            marcadores = ",".join("?" for _ in lote)
            linhas = conn.execute(
                "SELECT cnes, municipio_codigo FROM procedimentos_realizados "
                f"WHERE cnes IN ({marcadores}) AND municipio_codigo IS NOT NULL "
                "AND municipio_codigo<>''",
                lote,
            ).fetchall()
            for linha in linhas:
                mapa.setdefault(linha["cnes"], linha["municipio_codigo"])
    return mapa


def atualizar_cache(forcar: bool = False) -> int:
    if forcar:
        with conexao() as conn:
            linhas = conn.execute(
                "SELECT DISTINCT cnes FROM procedimentos_realizados "
                "WHERE cnes IS NOT NULL AND cnes<>''"
            ).fetchall()
        pendentes = sorted(r["cnes"] for r in linhas)
        with transacao() as conn:
            conn.execute("DELETE FROM estabelecimentos")
    else:
        pendentes = codigos_sem_nome()

    if not pendentes:
        print("[estabelecimentos] Todos os nomes já estão no cache.")
        return 0

    municipio_por_cnes = _municipios_por_cnes(pendentes)
    por_municipio: dict[str, list[str]] = {}
    for cnes in pendentes:
        municipio = municipio_por_cnes.get(cnes)
        if municipio:
            por_municipio.setdefault(municipio, []).append(cnes)

    linhas_gravar: list[tuple[str, str | None, str | None, str]] = []
    erros = 0
    for indice, (municipio, codigos) in enumerate(sorted(por_municipio.items()), 1):
        try:
            base = _buscar_por_municipio(municipio)
        except Exception as exc:  # noqa: BLE001
            erros += 1
            print(f"[estabelecimentos] Município {municipio}: {type(exc).__name__}: {exc}")
            continue
        for cnes in codigos:
            dados = base.get(cnes)
            if dados and any(dados):
                linhas_gravar.append((cnes, dados[0], dados[1], _agora()))
        if indice % 25 == 0:
            print(f"[estabelecimentos] {indice}/{len(por_municipio)} municípios; {len(linhas_gravar)} nomes.")
        time.sleep(PAUSA_ENTRE_CONSULTAS)

    if linhas_gravar:
        with transacao() as conn:
            conn.executemany(
                "INSERT INTO estabelecimentos (cnes,razao_social,nome_fantasia,atualizado_em) "
                "VALUES (?,?,?,?) ON CONFLICT(cnes) DO UPDATE SET "
                "razao_social=excluded.razao_social,nome_fantasia=excluded.nome_fantasia," 
                "atualizado_em=excluded.atualizado_em",
                linhas_gravar,
            )

    print(f"[estabelecimentos] Concluído: {len(linhas_gravar)}/{len(pendentes)} nomes; {erros} erros.")
    return len(linhas_gravar)
