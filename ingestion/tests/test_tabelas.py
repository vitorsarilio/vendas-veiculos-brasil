import pytest
from conftest import CABECALHO, PaginaFalsa, PlumberFalso

from ingestao import tabelas


def test_mes_do_relatorio(paginas):
    assert tabelas.mes_do_relatorio(paginas) == "2023-12"


def test_resumo_le_os_tres_segmentos_e_ignora_caminhoes(paginas):
    linhas = {r["segmento"]: r for r in tabelas.resumo_segmentos(paginas)}
    assert set(linhas) == {"automoveis", "comerciais_leves", "leves"}
    assert linhas["leves"]["mes_atual"] == "236.597"
    assert linhas["automoveis"]["acumulado_ano_anterior"] == "1.576.000"


def test_resumo_ausente_falha():
    with pytest.raises(tabelas.TabelaNaoEncontrada):
        tabelas.resumo_segmentos([PaginaFalsa(1, CABECALHO + ["Outra coisa"])])


def test_ranking_separa_autos_comerciais_e_total(paginas):
    linhas = tabelas.ranking_marcas(paginas)
    por_segmento = {}
    for linha in linhas:
        por_segmento.setdefault(linha["segmento"], []).append(linha["marca"])
    assert por_segmento == {"automoveis": ["FIAT", "VW", "GM"], "comerciais_leves": ["FIAT", "TOYOTA"], "leves": ["FIAT", "VW"]}
    assert linhas[0] == {"segmento": "automoveis", "posicao": "1", "marca": "FIAT", "quantidade": "40.000", "participacao": "21,51%"}


def test_ranking_do_mes_nao_usa_a_pagina_acumulada(paginas):
    # A página acumulada não tem linhas; se fosse escolhida, a leitura falharia.
    assert tabelas.ranking_marcas(paginas)


@pytest.mark.parametrize(
    "linha, esperado",
    [
        ("1º FIAT/MOBI 6.367 7.395 73.428 51,36%", ("FIAT/MOBI", "6.367", "7.395", "73.428")),
        ("3º VW/UP 0 0 = 6 0,00%", ("VW/UP", "0", "0", "6")),  # '=' solto entre as colunas
        ("1º GWM/ORA 03 61 711 775 0,16%", ("GWM/ORA 03", "61", "711", "775")),  # nome termina em número
        ("1º FIAT/STRADA 0,00 10.000 120.000 70,00%", ("FIAT/STRADA", "0,00", "10.000", "120.000")),  # zero como 0,00
    ],
)
def test_linha_de_modelo(linha, esperado):
    r = tabelas._separar_linha_de_modelo(linha)
    assert (r["modelo"], r["mes_anterior"], r["mes_atual"], r["acumulado_ano"]) == esperado


def test_linha_sem_percentual_nao_e_modelo():
    assert tabelas._separar_linha_de_modelo("1º FIAT 40.000") is None


def test_modelos_guardam_segmento_e_categoria_e_param_nos_caminhoes(paginas):
    modelos = tabelas.modelos_por_categoria(paginas)
    assert [(m["segmento"], m["categoria"], m["modelo"]) for m in modelos] == [
        ("automoveis", "Veículos de Entrada", "FIAT/MOBI"),
        ("automoveis", "Veículos de Entrada", "RENAULT/KWID"),
        ("automoveis", "Veículos de Entrada", "VW/UP"),
        ("automoveis", "Hatch Pequenos", "GWM/ORA 03"),
        ("comerciais_leves", "Pick-up's Pequenas", "FIAT/STRADA"),
    ]


def test_totais_por_categoria(paginas):
    totais = tabelas.totais_por_categoria(paginas)
    assert [(t["categoria"], t["mes_atual"]) for t in totais] == [("Veículos de Entrada", "15.499"), ("Hatch Pequenos", "711")]


def _pagina_de_canal(rotulos):
    """rotulos: (texto, y, azul?) — cada rótulo dentro de um quadrado da cor da fatia."""
    curvas, palavras = [], []
    for texto, y, azul in rotulos:
        cor = (0.141, 0.247, 0.4) if azul else (0.639, 0.639, 0.639)
        curvas.append({"fill": True, "non_stroking_color": cor, "pts": [(0, y - 5), (100, y - 5), (100, y + 5), (0, y + 5)]})
        palavras.append({"text": texto, "x0": 40, "x1": 60, "top": y - 3, "bottom": y + 3})
    return PaginaFalsa(24, CABECALHO + ["Participação de venda direta e venda varejo Setembro/2026"],
                       pagina=PlumberFalso(curves=curvas, palavras=palavras))


def test_canal_pela_cor_da_fatia():
    pagina = _pagina_de_canal([
        ("46.3%", 200, True), ("53.7%", 220, False),
        ("39%", 400, False), ("61%", 420, True),
        ("50.9%", 620, False), ("49.1%", 640, True),
    ])
    assert tabelas.canal_em_texto([pagina]) == [
        {"segmento": "automoveis", "venda_direta_pct": "46.3", "varejo_pct": "53.7"},
        {"segmento": "comerciais_leves", "venda_direta_pct": "61", "varejo_pct": "39"},
        {"segmento": "leves", "venda_direta_pct": "49.1", "varejo_pct": "50.9"},
    ]


def test_canal_em_imagem_devolve_none():
    pagina = PaginaFalsa(20, CABECALHO + ["Participação de venda direta e venda varejo Dezembro/2012"])
    assert tabelas.canal_em_texto([pagina]) is None


def test_canal_com_duas_fatias_iguais_falha():
    pagina = _pagina_de_canal([
        ("46.3%", 200, True), ("53.7%", 220, True),
        ("39%", 400, False), ("61%", 420, True),
        ("50.9%", 620, False), ("49.1%", 640, True),
    ])
    with pytest.raises(tabelas.TabelaNaoEncontrada, match="um rótulo de cada canal"):
        tabelas.canal_em_texto([pagina])


def test_resumo_com_rotulo_abaixo_dos_numeros():
    # abr/2017: o rótulo sai uma linha abaixo dos números
    pagina = PaginaFalsa(1, CABECALHO + [
        "Resumo Mensal Abril de 2017",
        "131.516 158.068 523.342 131.961 533.582 -16,80 -0,34 -1,92", "A) Autos",
        "20.867 25.764 88.825 25.547 88.952 -19,01 -18,32 -0,14", "B) Com. Leves",
        "152.383 183.832 612.167 157.508 622.534 -17,11 -3,25 -1,67", "A + B",
    ])
    linhas = {r["segmento"]: r["mes_atual"] for r in tabelas.resumo_segmentos([pagina])}
    assert linhas == {"automoveis": "131.516", "comerciais_leves": "20.867", "leves": "152.383"}


def test_automoveis_pela_diferenca_quando_a_tabela_e_imagem():
    # jan/2022: a tabela de automóveis é imagem; comerciais leves vai até marcas de 1 unidade
    pagina = PaginaFalsa(
        8, CABECALHO + ["Ranking por marca Janeiro/2022"],
        esquerda=["AUTOMÓVEIS", "AUTOMÓVEIS + COMERCIAIS LEVES", "1º FIAT 23.299 19,98%", "2º GM 13.104 11,24%", "3º JEEP 11.352 9,74%"],
        direita=["COMERCIAIS LEVES", "1º FIAT 11.815 48,44%", "2º GM 742 3,04%", "3º GWM 1 0,00%"],
    )
    autos = [(r["marca"], r["quantidade"]) for r in tabelas.ranking_marcas([pagina]) if r["segmento"] == "automoveis"]
    assert autos == [("GM", "12.362"), ("FIAT", "11.484"), ("JEEP", "11.352")]


def test_sem_automoveis_e_com_comerciais_cortado_falha():
    pagina = PaginaFalsa(
        8, CABECALHO + ["Ranking por marca Janeiro/2022"],
        esquerda=["AUTOMÓVEIS", "AUTOMÓVEIS + COMERCIAIS LEVES", "1º FIAT 23.299 19,98%"],
        direita=["COMERCIAIS LEVES", "1º FIAT 11.815 48,44%", "2º GM 742 3,04%"],
    )
    with pytest.raises(tabelas.TabelaNaoEncontrada):
        tabelas.ranking_marcas([pagina])


def test_cabecalho_com_letras_dobradas_nao_vira_categoria():
    pagina = PaginaFalsa(11, CABECALHO + [
        "Modelos mais emplacados acumulado até Jan/2022", "AUTOMÓVEIS", "Hatch Pequenos",
        "DDeezz JJaann AAccuummuullaaddoo", "1º VW/POLO 10.196 17.999 111.242 23,40%",
    ])
    assert tabelas.modelos_por_categoria([pagina])[0]["categoria"] == "Hatch Pequenos"
