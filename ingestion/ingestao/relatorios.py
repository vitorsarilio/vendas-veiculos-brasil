"""Lista oficial de relatórios e cópia local dos PDFs."""

import hashlib
import logging
import re
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import requests

from ingestao.config import (
    CORRECOES_DA_LISTA,
    MESES_REBAIXADOS,
    PAUSA_ENTRE_DOWNLOADS_S,
    PRIMEIRO_ANO,
    URL_ARQUIVO,
    URL_LISTA,
)
from ingestao.rede import TIMEOUT, NaoEPdf, baixar_pdf

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Relatorio:
    mes: str  # "AAAA-MM", mês a que os dados se referem
    link: str  # nome do arquivo no portal

    @property
    def versao(self) -> int:
        # Nomes antigos trazem um contador na frente ("6_2012_12_2.pdf"); quando o portal lista
        # dois arquivos para o mesmo mês (ex.: jun/2019: 2019_06_2.pdf e 2_2019_06_2.pdf),
        # o de contador maior é a republicação. Sem contador conta como versão 1.
        achado = re.match(r"^(\d+)_\d{4}_", self.link)
        return int(achado.group(1)) if achado else 1

    @property
    def arquivo_local(self) -> str:
        return f"{self.mes}__{self.link}"


def consultar_ano(sessao: requests.Session, ano: int) -> list[Relatorio]:
    resposta = sessao.post(URL_LISTA, data={"ano": str(ano)}, timeout=TIMEOUT)
    resposta.raise_for_status()
    blocos = resposta.json().get("data", {}).get("blocos") or []
    relatorios = []
    for bloco in blocos:
        mes = str(bloco.get("data", ""))[:7]
        link = str(bloco.get("link") or "").strip()
        if not re.fullmatch(r"\d{4}-\d{2}", mes) or not link.lower().endswith(".pdf"):
            raise ValueError(f"Item inesperado na lista de {ano}: {bloco!r}")
        relatorios.append(Relatorio(mes, link))
    return relatorios


def escolher_um_por_mes(relatorios: list[Relatorio]) -> tuple[list[Relatorio], list[dict]]:
    """Um relatório por mês. Devolve também as duplicatas descartadas, para o manifesto."""
    por_mes: dict[str, list[Relatorio]] = {}
    for rel in relatorios:
        por_mes.setdefault(rel.mes, []).append(rel)
    escolhidos, descartados = [], []
    for mes in sorted(por_mes):
        candidatos = sorted(por_mes[mes], key=lambda r: (r.versao, r.link))
        escolhido = candidatos[-1]
        escolhidos.append(escolhido)
        descartados += [{"mes": mes, "descartado": r.link, "usado": escolhido.link} for r in candidatos[:-1]]
    return escolhidos, descartados


def listar_relatorios(sessao: requests.Session, hoje: date | None = None) -> tuple[list[Relatorio], list[dict]]:
    hoje = hoje or date.today()
    todos = []
    for ano in range(PRIMEIRO_ANO, hoje.year + 1):
        todos += consultar_ano(sessao, ano)
        time.sleep(PAUSA_ENTRE_DOWNLOADS_S / 2)
    if not todos:
        raise RuntimeError("A lista oficial da Fenabrave veio vazia")
    return escolher_um_por_mes(corrigir_lista(todos))


def corrigir_lista(relatorios: list[Relatorio]) -> list[Relatorio]:
    """Troca os links que a lista oficial aponta para o mês errado (ver CORRECOES_DA_LISTA)."""
    corrigidos = [r for r in relatorios if r.mes not in CORRECOES_DA_LISTA]
    corrigidos += [Relatorio(mes, link) for mes, link in CORRECOES_DA_LISTA.items() if any(r.mes == mes for r in relatorios)]
    return corrigidos


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def atualizar_copia_local(sessao: requests.Session, relatorios: list[Relatorio], dir_pdfs: Path) -> list[dict]:
    """Baixa só o que falta, mais os últimos meses (podem ter sido republicados).

    Devolve uma linha por relatório para o manifesto: arquivo, sha256, se foi baixado agora
    e, quando não deu para baixar, o motivo.
    """
    dir_pdfs.mkdir(parents=True, exist_ok=True)
    recentes = {r.mes for r in relatorios[-MESES_REBAIXADOS:]}
    situacao = []
    baixados = 0
    for rel in relatorios:
        destino = dir_pdfs / rel.arquivo_local
        linha = {"mes": rel.mes, "link": rel.link, "arquivo": rel.arquivo_local}
        if destino.exists() and rel.mes not in recentes:
            linha["baixado_agora"] = False
        else:
            try:
                baixar_pdf(sessao, URL_ARQUIVO.format(link=rel.link), destino)
                linha["baixado_agora"] = True
                baixados += 1
                time.sleep(PAUSA_ENTRE_DOWNLOADS_S)
            except (requests.HTTPError, NaoEPdf) as erro:
                if not destino.exists():
                    log.warning("Sem PDF para %s (%s): %s", rel.mes, rel.link, erro)
                    linha["erro"] = str(erro)
                    situacao.append(linha)
                    continue
                log.warning("Não deu para atualizar %s; mantendo a cópia local: %s", rel.mes, erro)
                linha["baixado_agora"] = False
        linha["sha256"] = sha256(destino)
        situacao.append(linha)
    log.info("PDFs: %d na lista, %d baixados agora", len(relatorios), baixados)
    return situacao
