# -*- coding: utf-8 -*-
"""Configuração compartilhada dos testes: cada teste roda contra um
banco SQLite temporário e isolado (nunca o data/sih.db real)."""
import pytest

from datasus import settings
from datasus.db import inicializar_banco


@pytest.fixture(autouse=True)
def banco_temporario(tmp_path, monkeypatch):
    caminho = tmp_path / "teste_sih.db"
    monkeypatch.setattr(settings, "DB_PATH", caminho)
    inicializar_banco()
    yield caminho
