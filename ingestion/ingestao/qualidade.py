"""Conferências que falham alto antes do dbt: se o layout mudar, o pipeline para aqui
e o site continua com os marts da execução anterior."""

import logging
from collections import defaultdict
from decimal import Decimal

from ingestao.config import FAIXA_LEVES_MES, MESES_RESUMIDOS, PRIMEIRO_ANO, REVISOES_CONHECIDAS
from ingestao.pdf import inteiro

log = logging.getLogger(__name__)

# Diferença aceita entre a coluna "mês anterior" de um relatório e o "mês atual" do
# relatório anterior. A Fenabrave revisa alguns números depois de publicar.
REVISAO_MAXIMA = Decimal("0.02")


class QualidadeFalhou(Exception):
    def __init__(self, problemas: list[str]):
        self.problemas = problemas
        super().__init__(f"{len(problemas)} problema(s) nos dados extraídos:\n- " + "\n- ".join(problemas[:50]))


def _mes_seguinte(mes: str) -> str:
    ano, m = int(mes[:4]), int(mes[5:])
    return f"{ano + m // 12}-{m % 12 + 1:02d}"


def conferir_meses(meses: list[str]) -> list[str]:
    problemas = []
    if not meses:
        return ["nenhum relatório extraído"]
    if meses[0] != f"{PRIMEIRO_ANO}-01":
        problemas.append(f"a série começa em {meses[0]}, não em {PRIMEIRO_ANO}-01")
    for anterior, atual in zip(meses, meses[1:]):
        if atual != _mes_seguinte(anterior):
            problemas.append(f"lacuna entre {anterior} e {atual}")
    return problemas


def conferir_relatorio(r: dict) -> list[str]:
    """Conferências dentro de um mesmo relatório."""
    mes = r["mes"]
    problemas = [f"{mes}: {erro}" for erro in r["erros"]]
    if r.get("mes_no_pdf") and r["mes_no_pdf"] != mes:
        problemas.append(f"{mes}: o PDF diz ser de {r['mes_no_pdf']} (a lista oficial apontou o arquivo errado?)")

    segmentos = {s["segmento"]: inteiro(s["mes_atual"]) for s in r.get("fenabrave_segmentos") or []}
    if len(segmentos) == 3:
        if segmentos["automoveis"] + segmentos["comerciais_leves"] != segmentos["leves"]:
            problemas.append(f"{mes}: automóveis + comerciais leves ≠ leves ({segmentos})")
        minimo, maximo = FAIXA_LEVES_MES
        if not minimo <= segmentos["leves"] <= maximo:
            problemas.append(f"{mes}: total de leves fora da faixa plausível ({segmentos['leves']})")

    soma_marcas = defaultdict(int)
    for linha in r.get("fenabrave_marcas") or []:
        soma_marcas[linha["segmento"]] += inteiro(linha["quantidade"])
    for segmento, soma in soma_marcas.items():
        total = segmentos.get(segmento)
        if total is not None and soma > total:
            problemas.append(f"{mes}: marcas de {segmento} somam {soma}, mais que o total {total}")
        if total and soma < total * 0.8:
            problemas.append(f"{mes}: marcas de {segmento} cobrem só {soma / total:.0%} do total (ranking cortado?)")

    if mes not in MESES_RESUMIDOS and "fenabrave_modelos" in r:
        por_categoria = defaultdict(int)
        for linha in r["fenabrave_modelos"]:
            por_categoria[linha["categoria"]] += inteiro(linha["mes_atual"])
        for total in r.get("totais_modelos") or []:
            # A lista de cada categoria é um top N (e às vezes pula posições, ex.: jan/2008
            # vai de 7º a 10º); o Total inclui os modelos de fora. Só não pode passar dele.
            soma = por_categoria.get(total["categoria"], 0)
            if soma > inteiro(total["mes_atual"]):
                problemas.append(f"{mes}: modelos de '{total['categoria']}' somam {soma}, o total diz {total['mes_atual']}")

    canal = {c["segmento"]: c for c in r.get("fenabrave_canal") or []}
    if mes in MESES_RESUMIDOS:
        pass
    elif set(canal) != {"automoveis", "comerciais_leves", "leves"}:
        problemas.append(f"{mes}: canal incompleto ({sorted(canal)})")
    else:
        for segmento, c in canal.items():
            soma = Decimal(c["venda_direta_pct"]) + Decimal(c["varejo_pct"])
            if abs(soma - 100) > Decimal("0.11"):
                problemas.append(f"{mes}: canal de {segmento} soma {soma}%")
        if len(segmentos) == 3:
            # O % de leves é a média dos dois segmentos, ponderada pelo volume.
            direta = {s: Decimal(c["venda_direta_pct"]) for s, c in canal.items()}
            esperado = (direta["automoveis"] * segmentos["automoveis"] + direta["comerciais_leves"] * segmentos["comerciais_leves"]) / segmentos["leves"]
            if abs(esperado - direta["leves"]) > Decimal("1.0"):
                problemas.append(f"{mes}: % de venda direta de leves ({direta['leves']}) não bate com a média dos segmentos ({esperado:.2f})")
    return problemas


def conferir_continuidade(resultados: list[dict]) -> list[str]:
    """'Mês anterior' do relatório M contra o 'mês atual' do relatório M-1."""
    problemas = []
    atual = {}
    for r in resultados:
        for s in r.get("fenabrave_segmentos") or []:
            atual[(r["mes"], s["segmento"])] = s
    meses = sorted({mes for mes, _ in atual})
    anterior_de = {depois: antes for antes, depois in zip(meses, meses[1:]) if _mes_seguinte(antes) == depois}
    for r in resultados:
        mes_anterior = anterior_de.get(r["mes"])
        for s in r.get("fenabrave_segmentos") or []:
            s_anterior = atual.get((mes_anterior, s["segmento"]))
            if s_anterior is None or mes_anterior in REVISOES_CONHECIDAS:
                continue
            depois, antes = inteiro(s["mes_anterior"]), inteiro(s_anterior["mes_atual"])
            if antes and abs(depois - antes) / antes > REVISAO_MAXIMA:
                problemas.append(f"{r['mes']}: {s['segmento']} de {mes_anterior} era {antes}, agora {depois}")
    return problemas


def conferir(resultados: list[dict]) -> None:
    problemas = conferir_meses([r["mes"] for r in resultados])
    for r in resultados:
        problemas += conferir_relatorio(r)
    problemas += conferir_continuidade(resultados)
    if problemas:
        raise QualidadeFalhou(problemas)
    log.info("Qualidade: %d relatórios conferidos, nenhum problema", len(resultados))
