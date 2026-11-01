"""Cliente HTTP com retentativas: portais públicos às vezes oscilam."""

import logging
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ingestao.config import USER_AGENT

log = logging.getLogger(__name__)

TIMEOUT = (30, 120)  # (conexão, leitura) em segundos
TAMANHO_BLOCO = 1 << 20  # 1 MiB
ASSINATURA_PDF = b"%PDF-"


class NaoEPdf(Exception):
    """O servidor respondeu, mas não com um PDF (ex.: página HTML de "não encontrado")."""


def criar_sessao() -> requests.Session:
    sessao = requests.Session()
    # Esperas crescentes até 2 min, ~6,5 min no total, antes de desistir.
    # POST incluído: a consulta da lista oficial é um POST que só lê dados.
    retentativas = Retry(
        total=7,
        backoff_factor=5,  # 0, 10, 20, 40, 80, 120, 120 s
        backoff_max=120,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "POST"),
        respect_retry_after_header=True,
    )
    sessao.mount("https://", HTTPAdapter(max_retries=retentativas))
    sessao.headers["User-Agent"] = USER_AGENT
    return sessao


def baixar_pdf(sessao: requests.Session, url: str, destino: Path) -> int:
    """Baixa em streaming para um arquivo temporário e só renomeia no fim.

    Confere a assinatura %PDF- antes de aceitar: um endereço inexistente às vezes volta
    como página HTML, e isso não pode entrar no cache como se fosse relatório.
    """
    destino.parent.mkdir(parents=True, exist_ok=True)
    parcial = destino.with_name(destino.name + ".part")
    log.info("Baixando %s", url)
    with sessao.get(url, stream=True, timeout=TIMEOUT) as resposta:
        resposta.raise_for_status()
        with open(parcial, "wb") as arquivo:
            for bloco in resposta.iter_content(TAMANHO_BLOCO):
                arquivo.write(bloco)
    with open(parcial, "rb") as arquivo:
        inicio = arquivo.read(len(ASSINATURA_PDF))
    if inicio != ASSINATURA_PDF:
        parcial.unlink(missing_ok=True)
        raise NaoEPdf(f"{url} não devolveu um PDF (começa com {inicio!r})")
    parcial.replace(destino)
    return destino.stat().st_size
