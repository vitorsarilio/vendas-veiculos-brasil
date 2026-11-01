import copy

import pytest

from ingestao import qualidade


def relatorio(mes="2023-12", **trocas):
    r = {
        "mes": mes,
        "mes_no_pdf": mes,
        "erros": [],
        "fenabrave_segmentos": [
            {"segmento": "automoveis", "mes_atual": "186.000", "mes_anterior": "165.233"},
            {"segmento": "comerciais_leves", "mes_atual": "50.597", "mes_anterior": "47.100"},
            {"segmento": "leves", "mes_atual": "236.597", "mes_anterior": "212.333"},
        ],
        "fenabrave_marcas": [
            {"segmento": "automoveis", "quantidade": "180.000"},
            {"segmento": "comerciais_leves", "quantidade": "50.000"},
            {"segmento": "leves", "quantidade": "230.000"},
        ],
        "fenabrave_modelos": [{"categoria": "Hatch", "mes_atual": "700"}, {"categoria": "Hatch", "mes_atual": "11"}],
        "totais_modelos": [{"categoria": "Hatch", "mes_atual": "711"}],
        "fenabrave_canal": [
            {"segmento": "automoveis", "venda_direta_pct": "40.00", "varejo_pct": "60.00"},
            {"segmento": "comerciais_leves", "venda_direta_pct": "60.00", "varejo_pct": "40.00"},
            {"segmento": "leves", "venda_direta_pct": "44.28", "varejo_pct": "55.72"},
        ],
    }
    r.update(trocas)
    return r


def test_relatorio_coerente_passa():
    assert qualidade.conferir_relatorio(relatorio()) == []


def test_pdf_de_outro_mes():
    assert "lista oficial apontou" in qualidade.conferir_relatorio(relatorio(mes_no_pdf="2024-01"))[0]


def test_segmentos_que_nao_somam():
    r = relatorio()
    r["fenabrave_segmentos"][2]["mes_atual"] = "236.598"
    assert any("≠ leves" in p for p in qualidade.conferir_relatorio(r))


def test_marcas_acima_do_total():
    r = relatorio()
    r["fenabrave_marcas"][0]["quantidade"] = "190.000"
    assert any("mais que o total" in p for p in qualidade.conferir_relatorio(r))


def test_ranking_cortado_demais():
    r = relatorio()
    r["fenabrave_marcas"][0]["quantidade"] = "100.000"
    assert any("cobrem só" in p for p in qualidade.conferir_relatorio(r))


def test_modelos_acima_do_total_da_categoria():
    r = relatorio(totais_modelos=[{"categoria": "Hatch", "mes_atual": "710"}])
    assert any("somam 711" in p for p in qualidade.conferir_relatorio(r))


def test_modelos_abaixo_do_total_e_o_top_n():
    assert qualidade.conferir_relatorio(relatorio(totais_modelos=[{"categoria": "Hatch", "mes_atual": "900"}])) == []


def test_canal_que_nao_soma_100():
    r = relatorio()
    r["fenabrave_canal"][0]["varejo_pct"] = "61.00"
    assert any("soma 101" in p for p in qualidade.conferir_relatorio(r))


def test_canal_de_leves_fora_da_media_dos_segmentos():
    # Pega canais trocados: se o OCR inverter venda direta e varejo num segmento, a média não fecha.
    r = relatorio()
    r["fenabrave_canal"][2] = {"segmento": "leves", "venda_direta_pct": "55.72", "varejo_pct": "44.28"}
    assert any("média dos segmentos" in p for p in qualidade.conferir_relatorio(r))


def test_canal_faltando():
    assert any("canal incompleto" in p for p in qualidade.conferir_relatorio(relatorio(fenabrave_canal=[])))


def test_lacuna_e_inicio_da_serie():
    assert qualidade.conferir_meses(["2003-01", "2003-02", "2003-04"]) == ["lacuna entre 2003-02 e 2003-04"]
    assert "começa em 2003-02" in qualidade.conferir_meses(["2003-02"])[0]
    assert qualidade.conferir_meses(["2003-01", "2003-02"]) == []


def test_virada_de_ano_nao_e_lacuna():
    assert qualidade.conferir_meses(["2003-01", *[f"2003-{m:02d}" for m in range(2, 13)], "2004-01"]) == []


def test_continuidade_aceita_revisao_pequena_e_pega_a_grande():
    nov = relatorio("2023-11")
    dez = copy.deepcopy(relatorio("2023-12"))
    for s, valor in zip(dez["fenabrave_segmentos"], ["186.100", "50.597", "236.697"]):
        s["mes_anterior"] = valor  # revisão de 0,05% em autos
    for s, valor in zip(nov["fenabrave_segmentos"], ["186.000", "50.597", "236.597"]):
        s["mes_atual"] = valor
    assert qualidade.conferir_continuidade([nov, dez]) == []
    dez["fenabrave_segmentos"][1]["mes_anterior"] = "60.000"
    assert qualidade.conferir_continuidade([nov, dez]) == ["2023-12: comerciais_leves de 2023-11 era 50597, agora 60000"]


def test_conferir_junta_todos_os_problemas():
    with pytest.raises(qualidade.QualidadeFalhou) as erro:
        qualidade.conferir([relatorio("2003-01", erros=["fenabrave_marcas: falhou"]), relatorio("2003-03")])
    assert any("lacuna" in p for p in erro.value.problemas)
    assert any("fenabrave_marcas: falhou" in p for p in erro.value.problemas)
