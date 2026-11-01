"""Extração única do % de venda direta das pizzas em imagem (jan/2003 → jun/2024).

Gera ingestion/ingestao/dados/canal_pizzas_imagem.csv. Não roda no pipeline: os relatórios
antigos não mudam, então o resultado fica versionado. Precisa de dependências extras, fora
do requirements.txt:

    pip install rapidocr-onnxruntime==1.2.3 numpy
    python scripts/recuperar_canal_imagens.py data/pdfs

Para cada pizza:
1. lê os rótulos "NN.NN%" por OCR (RapidOCR, Apache 2.0). Em 9 pizzas de 2024 os rótulos
   já são texto no PDF, e são lidos direto;
2. decide qual rótulo é a venda direta pela posição: a fatia escura (venda direta) começa
   às 3 horas e gira no sentido horário, então o meio dela fica sempre na metade de baixo
   da pizza, e o rótulo também. Com um rótulo só, o outro é o complemento para 100%;
3. confere pelo ângulo da fatia escura medido na imagem (tolerância de 5 p.p., porque a
   perspectiva 3D distorce o ângulo);
4. confere o mês inteiro: o % de leves tem que ser a média de automóveis e comerciais
   leves ponderada pelos volumes do resumo. Isso pega qualquer dígito lido errado.

As 6 pizzas em que o OCR não achou os rótulos foram lidas olhando a imagem (LEITURA_MANUAL)
e passaram pelas mesmas conferências.
"""

import csv
import re
import sys
from pathlib import Path

import numpy as np
import pdfplumber
from rapidocr_onnxruntime import RapidOCR

from ingestao import tabelas
from ingestao.config import ARQUIVO_CANAL_IMAGEM, MESES_RECONSTRUIDOS, MESES_RESUMIDOS
from ingestao.pdf import _decodificar_cid, abrir, inteiro, sem_acento

ULTIMO_MES_EM_IMAGEM = "2024-06"  # de jul/2024 em diante a pizza é vetorial (tabelas.canal_em_texto)
SEGMENTOS = ["automoveis", "comerciais_leves", "leves"]
PAGINAS_FIXAS = {"2023-09": 21}  # set/2023 não tem texto para achar a página pelo título
LEITURA_MANUAL = {
    ("2003-06", "comerciais_leves"): 35.54,
    ("2016-09", "leves"): 35.68,
    ("2018-01", "leves"): 33.54,
    ("2021-03", "automoveis"): 41.69,
    ("2022-10", "automoveis"): 50.97,
    ("2022-10", "comerciais_leves"): 63.20,
}
# Volumes de set/2023 (mês reconstruído), para a conferência da média ponderada.
VOLUMES_FIXOS = {"2023-09": {"automoveis": 145676, "comerciais_leves": 41754, "leves": 187430}}

ocr = RapidOCR()


def pagina_mensal(doc, mes):
    if mes in PAGINAS_FIXAS:
        return doc.pages[PAGINAS_FIXAS[mes] - 1]
    for pagina in doc.pages[12:40]:
        topo = sem_acento(_decodificar_cid(pagina.crop((0, 0, pagina.width, 110)).extract_text() or ""))
        if "venda direta e venda varejo" in topo:
            return pagina
    raise RuntimeError(f"{mes}: página de varejo × venda direta não encontrada")


def pizzas(pagina):
    """As 3 pizzas mensais, de cima para baixo. Em set/2023 cada uma vem em duas metades."""
    blocos = []
    for im in sorted((im for im in pagina.images if im["width"] > 300), key=lambda im: im["top"]):
        anterior = blocos[-1] if blocos else None
        if anterior and abs(im["x0"] - anterior["x0"]) < 2 and im["top"] - anterior["bottom"] < 6 and anterior["partes"] < 2:
            anterior["bottom"], anterior["partes"] = im["bottom"], 2
        else:
            blocos.append({"x0": im["x0"], "x1": im["x1"], "top": im["top"], "bottom": im["bottom"], "partes": 1})
    if len(blocos) != 3:
        raise RuntimeError(f"esperava 3 pizzas, achei {len(blocos)}")
    return blocos


def _cor(px, azul: bool):
    r, g, b = (px[..., i].astype(int) for i in range(3))
    if azul:
        return (b - r > 25) & (b < 200) & (r < 120)
    branco = (r > 245) & (g > 245) & (b > 245)
    return (r > 200) & (g > 200) & (b > 190) & (r < 250) & (abs(r - b) < 25) & ~branco


def geometria(img):
    """(% da fatia escura pelo ângulo, linha do centro da pizza na imagem)."""
    area = img[:, : int(img.shape[1] * 0.72)]  # a legenda fica à direita
    azul = _cor(area, azul=True)
    ys, xs = np.nonzero(azul | _cor(area, azul=False))
    if len(xs) < 1000 or azul.sum() < 30:
        return None, None
    xmin, xmax = np.percentile(xs, 0.2), np.percentile(xs, 99.8)
    cx, a = (xmin + xmax) / 2, (xmax - xmin) / 2
    # Centro vertical: a borda de cima da fatia escura junto à borda direita (o raio das 3 horas).
    linhas_azuis = np.nonzero(azul[:, int(cx + a * 0.6): int(cx + a * 0.95)].any(axis=1))[0]
    if len(linhas_azuis) == 0:
        return None, None
    cy = float(linhas_azuis.min())
    b = cy - np.percentile(ys, 0.2)
    if b <= 5:
        return None, cy
    ya, xa = np.nonzero(azul)
    u, v = (xa - cx) / a, (ya - cy) / b
    ang = (np.degrees(np.arctan2(v, u)[np.hypot(u, v) < 0.95]) + 360) % 360
    ang = ang[(ang > 0.5) & (ang < 359.5)]
    return (float(np.percentile(ang, 99.5)) / 3.6 if len(ang) else None), cy


def rotulos_por_ocr(img):
    resultado, _ = ocr(img)
    valores = []
    for caixa, texto, _conf in resultado or []:
        y = sum(ponto[1] for ponto in caixa) / 4
        valores += [(float(f"{i}.{d}"), y) for i, d in re.findall(r"(\d{1,3})[.,](\d{2})%", texto.replace(" ", ""))]
    return valores


def decidir(rotulos, geo, cy):
    if len(rotulos) == 2 and abs(rotulos[0][0] + rotulos[1][0] - 100) < 0.015:
        de_baixo, de_cima = sorted(rotulos, key=lambda r: r[1], reverse=True)
        if cy is not None and not de_baixo[1] > cy > de_cima[1]:
            return None, None
        direta, origem = de_baixo[0], "imagem_ocr"
    elif len(rotulos) == 1 and cy is not None:
        valor, y = rotulos[0]
        direta, origem = (valor if y > cy else round(100 - valor, 2)), "imagem_ocr_complemento"
    else:
        return None, None
    if geo is None or abs(direta - geo) >= 5:
        return None, None
    return direta, origem


def ler_mes(caminho: Path, mes: str) -> dict[str, tuple[float, str]]:
    resultado = {}
    with pdfplumber.open(caminho) as doc:
        pagina = pagina_mensal(doc, mes)
        palavras = [w for w in pagina.extract_words() if re.fullmatch(r"\d+[.,]\d+%", _decodificar_cid(w["text"]))]
        for segmento, p in zip(SEGMENTOS, pizzas(pagina)):
            caixa = (p["x0"], p["top"], p["x1"], p["bottom"])
            img = np.asarray(pagina.crop(caixa).to_image(resolution=300).original.convert("RGB"))
            geo, cy = geometria(img)
            em_texto = [(float(_decodificar_cid(w["text"]).replace(",", ".").rstrip("%")), ((w["top"] + w["bottom"]) / 2 - p["top"]) * 300 / 72)
                        for w in palavras if p["top"] <= w["top"] <= p["bottom"]]
            if (mes, segmento) in LEITURA_MANUAL:
                direta, origem = LEITURA_MANUAL[(mes, segmento)], "imagem_leitura_manual"
                if geo is None or abs(direta - geo) >= 5:
                    raise RuntimeError(f"{mes} {segmento}: leitura manual {direta} não confere com a geometria {geo}")
            elif len(em_texto) == 2:
                direta, origem = decidir(em_texto, geo, cy)
                origem = origem and "imagem_texto_sobreposto"
            else:
                direta, origem = decidir(rotulos_por_ocr(img), geo, cy)
            if direta is None:
                raise RuntimeError(f"{mes} {segmento}: sem leitura confiável; olhar a imagem e incluir em LEITURA_MANUAL")
            resultado[segmento] = (direta, origem)
    return resultado


def volumes(caminho: Path, mes: str) -> dict[str, int]:
    if mes in VOLUMES_FIXOS:
        return VOLUMES_FIXOS[mes]
    doc, paginas = abrir(caminho)
    try:
        return {s["segmento"]: inteiro(s["mes_atual"]) for s in tabelas.resumo_segmentos(paginas)}
    finally:
        doc.close()


def main(dir_pdfs: Path) -> None:
    linhas = []
    for caminho in sorted(dir_pdfs.glob("*.pdf")):
        mes = caminho.name[:7]
        if mes > ULTIMO_MES_EM_IMAGEM or mes in MESES_RESUMIDOS:
            continue
        canal = ler_mes(caminho, mes)
        v = volumes(caminho, mes)
        d = {s: canal[s][0] for s in SEGMENTOS}
        esperado = (d["automoveis"] * v["automoveis"] + d["comerciais_leves"] * v["comerciais_leves"]) / v["leves"]
        if abs(esperado - d["leves"]) > 0.01:
            raise RuntimeError(f"{mes}: leves {d['leves']} ≠ média ponderada {esperado:.3f}")
        for segmento in SEGMENTOS:
            direta, origem = canal[segmento]
            linhas.append({"mes": mes, "segmento": segmento, "venda_direta_pct": f"{direta:.2f}",
                           "varejo_pct": f"{100 - direta:.2f}", "origem": origem})
        print(mes, d, flush=True)
    assert all(m in {l["mes"] for l in linhas} for m in MESES_RECONSTRUIDOS)
    with open(ARQUIVO_CANAL_IMAGEM, "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(linhas[0]), lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(linhas)
    print(f"{len(linhas)} linhas gravadas em {ARQUIVO_CANAL_IMAGEM}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
