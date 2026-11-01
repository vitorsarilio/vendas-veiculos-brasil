import pytest

from ingestao.pdf import _decodificar_cid, inteiro


def test_fonte_sem_mapa_de_caracteres():
    # abr/2020: "(cid:36)" = "A", espaço = 3, "º" e acentos pela tabela própria
    texto = "(cid:36)(cid:12)(cid:3)(cid:36)(cid:88)(cid:87)(cid:82)(cid:86) (cid:20)(cid:158) S(cid:109)o"
    assert _decodificar_cid(texto) == "A) Autos 1º São"


def test_codigo_desconhecido_vira_marcador():
    assert _decodificar_cid("(cid:250)") == "�"


@pytest.mark.parametrize("valor, esperado", [("1.234", 1234), ("343.743", 343743), ("1.065.888", 1065888),
                                             ("5", 5), ("0,00", 0), ("-", 0)])
def test_inteiro(valor, esperado):
    assert inteiro(valor) == esperado


@pytest.mark.parametrize("valor", ["12,5", "1.23", "abc", ""])
def test_inteiro_rejeita_o_que_nao_e_contagem(valor):
    with pytest.raises(ValueError):
        inteiro(valor)
