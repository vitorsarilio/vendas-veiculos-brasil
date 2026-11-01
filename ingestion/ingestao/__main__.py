"""Uso: python -m ingestao [--offline] [--dir-pdfs data/pdfs] [--dir-raw data/raw] [--processos N]"""

import argparse
import json
import logging
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from ingestao import extracao, qualidade
from ingestao.config import CORRECOES_DA_LISTA, DIR_PDFS, DIR_RAW, MESES_RECONSTRUIDOS, MESES_RESUMIDOS
from ingestao.parquet import registros_para_parquet
from ingestao.rede import criar_sessao
from ingestao.relatorios import atualizar_copia_local, listar_relatorios, sha256

log = logging.getLogger("ingestao")


def copia_local_sem_rede(dir_pdfs: Path) -> list[dict]:
    """Situação dos PDFs a partir só dos arquivos já baixados (nome: 'AAAA-MM__<link>')."""
    situacao = []
    for arquivo in sorted(dir_pdfs.glob("*.pdf")):
        achado = re.match(r"^(\d{4}-\d{2})__(.+)$", arquivo.name)
        if achado:
            situacao.append({"mes": achado.group(1), "link": achado.group(2), "arquivo": arquivo.name,
                             "baixado_agora": False, "sha256": sha256(arquivo)})
    if not situacao:
        raise RuntimeError(f"Nenhum PDF em {dir_pdfs}")
    return situacao


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Baixa os relatórios da Fenabrave e grava as tabelas em data/raw.")
    parser.add_argument("--offline", action="store_true", help="não consulta o portal; usa só os PDFs já baixados")
    parser.add_argument("--dir-pdfs", type=Path, default=DIR_PDFS)
    parser.add_argument("--dir-raw", type=Path, default=DIR_RAW)
    parser.add_argument("--processos", type=int, default=None, help="PDFs lidos em paralelo (padrão: núcleos da máquina)")
    args = parser.parse_args(argv)

    # Acentos corretos no log também em terminais do Windows que não usam UTF-8 por padrão
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("pdfminer").setLevel(logging.ERROR)  # avisos de fonte sem FontBBox, inofensivos
    inicio = time.monotonic()

    descartados = []
    if args.offline:
        situacao = copia_local_sem_rede(args.dir_pdfs)
    else:
        sessao = criar_sessao()
        relatorios, descartados = listar_relatorios(sessao)
        situacao = atualizar_copia_local(sessao, relatorios, args.dir_pdfs)

    resultados = extracao.extrair_tudo(situacao, args.dir_pdfs, args.processos)
    qualidade.conferir(resultados)

    args.dir_raw.mkdir(parents=True, exist_ok=True)
    tabelas = []
    for nome, registros in extracao.montar_tabelas(resultados).items():
        caminho = args.dir_raw / f"{nome}.parquet"
        linhas = registros_para_parquet(registros, extracao.COLUNAS[nome], caminho)
        tabelas.append({"tabela": nome, "arquivo": caminho.name, "linhas": linhas})
        log.info("%s: %d linhas", nome, linhas)

    meses = [r["mes"] for r in resultados]
    manifesto = {
        "executado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "duracao_s": round(time.monotonic() - inicio, 1),
        "fonte": "Fenabrave, Informativo - Emplacamentos (dados Renavam/Senatran)",
        "primeiro_mes": meses[0],
        "ultimo_mes": meses[-1],
        "relatorios": len(situacao),
        "baixados_agora": sum(1 for s in situacao if s.get("baixado_agora")),
        "sem_pdf": [s for s in situacao if "erro" in s],
        "duplicatas_descartadas": descartados,
        "correcoes_da_lista": CORRECOES_DA_LISTA,
        "meses_reconstruidos": MESES_RECONSTRUIDOS,
        "meses_resumidos": sorted(MESES_RESUMIDOS),
        "pdfs": [{k: s.get(k) for k in ("mes", "link", "sha256")} for s in situacao],
        "tabelas": tabelas,
    }
    (args.dir_raw / "_manifesto.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Ingestão concluída em %.0f s (%s a %s)", manifesto["duracao_s"], meses[0], meses[-1])


if __name__ == "__main__":
    main()
