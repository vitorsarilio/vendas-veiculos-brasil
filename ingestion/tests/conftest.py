"""Páginas falsas com o texto real dos relatórios (copiado de PDFs de 2003, 2012, 2023 e 2026).

Os leitores só usam o cabeçalho, as linhas, as metades esquerda/direita e, no canal, as
palavras e as fatias da pizza; as classes abaixo imitam só isso.
"""

from dataclasses import dataclass, field

import pytest

from ingestao.pdf import sem_acento


@dataclass
class PlumberFalso:
    width: float = 600
    height: float = 842
    curves: list = field(default_factory=list)
    palavras: list = field(default_factory=list)

    def extract_words(self):
        return self.palavras


@dataclass
class PaginaFalsa:
    numero: int
    linhas: list[str]
    esquerda: list[str] = field(default_factory=list)
    direita: list[str] = field(default_factory=list)
    pagina: PlumberFalso = field(default_factory=PlumberFalso)

    @property
    def cabecalho(self) -> list[str]:
        return self.linhas[:6]

    @property
    def texto(self) -> str:
        return "\n".join(self.linhas)

    @property
    def chave(self) -> str:
        return sem_acento(self.texto)

    def texto_da_regiao(self, x0, x1):
        return self.esquerda if x0 == 0 else self.direita


CABECALHO = ["Ed. 252", "Informativo - Emplacamentos", "São Paulo, Janeiro de 2024"]

RESUMO = PaginaFalsa(1, CABECALHO + [
    "Resumo Mensal Dezembro de 2023",
    "2023 2023 2023 2022 2022",
    "Segmentos Dez Nov Acumulado Dez Acumulado",
    "A) Autos 186.000 165.233 1.712.000 166.111 1.576.000 12,57 11,97 8,63",
    "B) Com. Leves 50.597 47.100 478.000 45.210 420.000 7,43 11,92 13,81",
    "A + B 236.597 212.333 2.190.000 211.321 1.996.000 11,43 11,96 9,72",
    "C) Caminhões 9.500 9.800 108.000 11.000 125.000 -3,06 -13,64 -13,60",
])

RANKING = PaginaFalsa(
    8,
    CABECALHO + ["Ranking por marca Dezembro/2023"],
    esquerda=[
        "AUTOMÓVEIS",
        "1º FIAT 40.000 21,51%",
        "2º VW 35.000 18,82%",
        "3º GM 30.000 16,13%",
        "AUTOMÓVEIS + COMERCIAIS LEVES",
        "1º FIAT 60.000 25,36%",
        "2º VW 40.000 16,91%",
    ],
    direita=[
        "COMERCIAIS LEVES",
        "1º FIAT 20.000 39,53%",
        "2º TOYOTA 8.000 15,81%",
    ],
)

RANKING_ACUMULADO = PaginaFalsa(9, CABECALHO + ["Ranking por marca acumulado até Dezembro/2023"])

MODELOS = PaginaFalsa(11, CABECALHO + [
    "Modelos mais emplacados acumulado até Dez/2023",
    "AUTOMÓVEIS",
    "Veículos de Entrada",
    "2023 2023 2023",
    "Modelo Part.",
    "Nov Dez Acumulado",
    "1º FIAT/MOBI 6.367 7.395 73.428 51,36%",
    "2º RENAULT/KWID 5.971 8.104 63.316 44,29%",
    "3º VW/UP 0 0 = 6 0,00%",
    "Total 12.338 15.499 136.750 100%",
    "Hatch Pequenos",
    "1º GWM/ORA 03 61 711 775 0,16%",
    "Total 61 711 775 100%",
    "www.fenabrave.org.br 11",
])

MODELOS_CL = PaginaFalsa(12, CABECALHO + [
    "Modelos mais emplacados acumulado até Dez/2023",
    "COMERCIAIS LEVES",
    "Pick-up's Pequenas",
    "1º FIAT/STRADA 0,00 10.000 120.000 70,00%",
])

CAMINHOES = PaginaFalsa(30, CABECALHO + ["Emplacamento Caminhões Dezembro/2023", "1º X 1 1 1 1%"])


@pytest.fixture
def paginas():
    return [RESUMO, RANKING, RANKING_ACUMULADO, MODELOS, MODELOS_CL, CAMINHOES]
