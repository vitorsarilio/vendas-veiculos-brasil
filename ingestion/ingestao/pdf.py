"""Leitura de páginas dos relatórios: texto por linhas, com as correções que a fonte exige."""

import logging
import re
import unicodedata
from dataclasses import dataclass, field
from functools import cached_property

import pdfplumber

log = logging.getLogger(__name__)

# Alguns PDFs (ex.: abr/2020) usam uma fonte sem mapa de caracteres: o texto sai como
# "(cid:36)(cid:88)(cid:87)(cid:82)". O código é o caractere deslocado de 29 posições
# ("(cid:36)" = "A", "(cid:19)" = "0", "(cid:3)" = espaço). Os acentos ficam fora dessa
# faixa e têm uma tabela própria, preenchida a partir dos arquivos reais.
DESLOCAMENTO_CID = 29
CID_ESPECIAIS: dict[int, str] = {
    # Levantados em abr/2020, pelo contexto de palavras conhecidas ("São", "Variação", "1º"...).
    105: "á", 106: "à", 109: "ã", 111: "ç", 112: "é", 114: "ê", 116: "í", 121: "ó", 125: "õ", 126: "ú",
    158: "º", 172: " ",  # 172 é o marcador gráfico entre as células da tabela
    180: "“", 181: "”",
    207: "Ó", 208: "Ó",  # a fonte usa o mesmo desenho em "AUTOMÓVEIS" e "Ônibus"
}
_RX_CID = re.compile(r"\(cid:(\d+)\)")


def _decodificar_cid(texto: str) -> str:
    def trocar(achado: re.Match) -> str:
        codigo = int(achado.group(1))
        if codigo in CID_ESPECIAIS:
            return CID_ESPECIAIS[codigo]
        caractere = codigo + DESLOCAMENTO_CID
        return chr(caractere) if 32 <= caractere < 127 else "�"

    return _RX_CID.sub(trocar, texto)


def sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn").lower()


ALTURA_CABECALHO = 140  # pontos a partir do topo; cobre o título nos layouts antigo e novo


@dataclass
class Pagina:
    """Uma página do relatório. O texto só é extraído quando alguém pede (é a parte lenta)."""

    numero: int
    pagina: object = field(repr=False)  # pdfplumber.page.Page

    @cached_property
    def texto(self) -> str:
        return _decodificar_cid(self.pagina.extract_text() or "")

    @cached_property
    def cabecalho(self) -> list[str]:
        """Linhas do topo da página (edição, data e título), sem ler a página inteira."""
        recorte = self.pagina.crop((0, 0, self.pagina.width, min(ALTURA_CABECALHO, self.pagina.height)))
        return [linha.strip() for linha in _decodificar_cid(recorte.extract_text() or "").splitlines() if linha.strip()]

    @property
    def linhas(self) -> list[str]:
        return [linha.strip() for linha in self.texto.splitlines() if linha.strip()]

    @property
    def chave(self) -> str:
        """Texto sem acento e em minúsculas, para achar títulos."""
        return sem_acento(self.texto)

    def texto_da_regiao(self, x0: float, x1: float) -> list[str]:
        recorte = self.pagina.crop((x0, 0, x1, self.pagina.height))
        return [linha.strip() for linha in _decodificar_cid(recorte.extract_text() or "").splitlines() if linha.strip()]


def abrir(caminho) -> tuple[pdfplumber.PDF, list[Pagina]]:
    documento = pdfplumber.open(caminho)
    return documento, [Pagina(i, pagina) for i, pagina in enumerate(documento.pages, 1)]


def inteiro(valor: str) -> int:
    """'1.234' → 1234. Os relatórios recentes escrevem zero como '0,00'; '-' também é zero."""
    valor = valor.strip()
    if valor in {"-", "0,00", "0,0"}:
        return 0
    if not re.fullmatch(r"\d{1,3}(\.\d{3})*|\d+", valor):
        raise ValueError(f"Não é um número inteiro do relatório: {valor!r}")
    return int(valor.replace(".", ""))
