# -*- coding: utf-8 -*-
from datasus.codigos import normalizar_codigo


def test_normalizar_codigo_zero_a_esquerda():
    assert normalizar_codigo("2078", 7) == "0002078"


def test_normalizar_codigo_float_do_pandas():
    assert normalizar_codigo(2001586.0, 7) == "2001586"


def test_normalizar_codigo_none():
    assert normalizar_codigo(None) is None


def test_normalizar_codigo_vazio():
    assert normalizar_codigo("", 7) is None
    assert normalizar_codigo("nan", 7) is None


def test_normalizar_codigo_sigtap_10_digitos():
    assert normalizar_codigo("505020092", 10) == "0505020092"
