"""Extrai as tabelas de todos os PDFs da cópia local.

Reprocessa a série inteira a cada execução: uma correção num leitor vale para todos os
meses de uma vez. Os PDFs são independentes, então rodam em paralelo.
"""

import csv
import logging
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from ingestao import tabelas
from ingestao.config import ARQUIVO_CANAL_IMAGEM, MESES_RECONSTRUIDOS, MESES_RESUMIDOS
from ingestao.pdf import abrir
from ingestao.reconstrucao import reconstruir_mes

log = logging.getLogger(__name__)

COLUNAS = {
    "fenabrave_segmentos": ["mes", "segmento", *tabelas.COLUNAS_RESUMO, "origem", "arquivo"],
    "fenabrave_marcas": ["mes", "segmento", "posicao", "marca", "quantidade", "participacao", "origem", "arquivo"],
    "fenabrave_modelos": [
        "mes", "segmento", "categoria", "posicao", "modelo",
        "mes_anterior", "mes_atual", "acumulado_ano", "participacao", "origem", "arquivo",
    ],
    "fenabrave_canal": ["mes", "segmento", "venda_direta_pct", "varejo_pct", "origem", "arquivo"],
}


def _silenciar_pdfminer() -> None:
    """Os processos filhos não herdam a configuração de log; sem isto, cada PDF antigo
    imprime dezenas de avisos inofensivos de fonte sem FontBBox."""
    logging.getLogger("pdfminer").setLevel(logging.ERROR)


def extrair_pdf(caminho: Path, mes: str) -> dict:
    """Todas as tabelas de um relatório. Erros de leitura voltam como texto, para o
    relatório de qualidade listar todos os meses com problema de uma vez."""
    resultado = {"mes": mes, "arquivo": caminho.name, "erros": []}
    documento, paginas = abrir(caminho)
    try:
        etapas = {
            "mes_no_pdf": tabelas.mes_do_relatorio,
            "fenabrave_segmentos": tabelas.resumo_segmentos,
            "fenabrave_marcas": tabelas.ranking_marcas,
        }
        if mes not in MESES_RESUMIDOS:
            etapas["fenabrave_canal"] = tabelas.canal_em_texto
            etapas["fenabrave_modelos"] = tabelas.modelos_por_categoria
            etapas["totais_modelos"] = tabelas.totais_por_categoria
        for nome, leitor in etapas.items():
            try:
                resultado[nome] = leitor(paginas)
            except Exception as erro:  # noqa: BLE001 - cada falha vira um item do relatório
                resultado["erros"].append(f"{nome}: {type(erro).__name__}: {erro}")
    finally:
        documento.close()
    return resultado


def ler_canal_imagem(caminho: Path = ARQUIVO_CANAL_IMAGEM) -> dict[str, list[dict]]:
    """Canal dos meses em que a pizza é imagem: extração única, guardada no repositório."""
    por_mes: dict[str, list[dict]] = {}
    with open(caminho, encoding="utf-8", newline="") as arquivo:
        for linha in csv.DictReader(arquivo):
            por_mes.setdefault(linha["mes"], []).append(linha)
    return por_mes


def extrair_tudo(relatorios: list[dict], dir_pdfs: Path, processos: int | None = None) -> list[dict]:
    """relatorios: linhas do manifesto de PDFs (mes, arquivo). Devolve um resultado por mês, em ordem."""
    disponiveis = [r for r in relatorios if "erro" not in r]
    arquivo_do_mes = {r["mes"]: r["arquivo"] for r in disponiveis}
    meses = sorted(arquivo_do_mes)
    with ProcessPoolExecutor(max_workers=processos, initializer=_silenciar_pdfminer) as executor:
        futuros = []
        for i, mes in enumerate(meses):
            if mes in MESES_RECONSTRUIDOS:
                if not 0 < i < len(meses) - 1:
                    raise RuntimeError(f"{mes} precisa dos relatórios vizinhos para ser reconstruído")
                futuros.append(executor.submit(
                    reconstruir_mes, mes, dir_pdfs / arquivo_do_mes[meses[i - 1]], dir_pdfs / arquivo_do_mes[meses[i + 1]]
                ))
            else:
                futuros.append(executor.submit(extrair_pdf, dir_pdfs / arquivo_do_mes[mes], mes))
        resultados = []
        for i, futuro in enumerate(futuros, 1):
            resultados.append(futuro.result())
            if i % 50 == 0 or i == len(futuros):
                log.info("Lidos %d de %d relatórios", i, len(futuros))
    for resultado in resultados:
        resultado["arquivo"] = arquivo_do_mes[resultado["mes"]]
        resultado["origem"] = "reconstruido_dos_vizinhos" if resultado["mes"] in MESES_RECONSTRUIDOS else "texto_pdf"
    canal_imagem = ler_canal_imagem()
    for resultado in resultados:
        if resultado.get("fenabrave_canal") is None and "fenabrave_canal" in resultado:
            linhas = canal_imagem.get(resultado["mes"], [])
            resultado["fenabrave_canal"] = [
                {k: l[k] for k in ("segmento", "venda_direta_pct", "varejo_pct", "origem")} for l in linhas
            ]
        else:
            for linha in resultado.get("fenabrave_canal") or []:
                linha["origem"] = "texto_pdf"
    log.info("Extraídos %d relatórios", len(resultados))
    return resultados


def montar_tabelas(resultados: list[dict]) -> dict[str, list[dict]]:
    """Junta os resultados por mês em uma lista de registros por tabela."""
    saida = {nome: [] for nome in COLUNAS}
    for resultado in resultados:
        for nome in COLUNAS:
            for linha in resultado.get(nome) or []:
                registro = {"mes": resultado["mes"], "origem": resultado["origem"], **linha, "arquivo": resultado["arquivo"]}
                saida[nome].append(registro)
    return saida
