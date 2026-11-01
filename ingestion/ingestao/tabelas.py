"""Leitores das tabelas do caderno de automóveis e comerciais leves.

A estrutura do relatório é a mesma de 2003 a 2026 (só a numeração das páginas muda),
então cada tabela é achada pelo título da página, nunca pelo número dela. Os valores
saem como texto, fiéis ao PDF; a conversão de tipos fica no staging do dbt. Os leitores
só convertem números para conferir somas (ver qualidade.py).
"""

import re

from ingestao.pdf import Pagina, inteiro, sem_acento

MESES = ["janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]

_RANK = r"(\d{1,3})\s*[º°o]"
_NUMERO = re.compile(r"^(\d{1,3}(\.\d{3})*|\d+|0,00|0,0|-)$")
_PERCENTUAL = re.compile(r"^-?\d+(,\d+)?%$")


class TabelaNaoEncontrada(Exception):
    pass


def _titulo(pagina: Pagina) -> str:
    """O título fica numa das primeiras linhas, depois do cabeçalho (Ed., Informativo, data)."""
    for linha in pagina.cabecalho[:8]:
        chave = sem_acento(linha)
        if not chave.startswith(("ed.", "informativo", "sao paulo", "dados de")) and len(chave) > 12:
            return chave
    return ""


def _caderno_de_leves(paginas: list[Pagina]) -> list[Pagina]:
    """Páginas de automóveis e comerciais leves: tudo antes do caderno de caminhões e ônibus."""
    resultado = []
    for pagina in paginas:
        if _titulo(pagina).startswith("emplacamento caminhoes"):
            break
        resultado.append(pagina)
    return resultado


# ---------- resumo mensal por segmento ----------

SEGMENTOS_RESUMO = {"a) autos": "automoveis", "b) com. leves": "comerciais_leves", "a + b": "leves"}
COLUNAS_RESUMO = ["mes_atual", "mes_anterior", "acumulado_ano", "mesmo_mes_ano_anterior", "acumulado_ano_anterior"]


def mes_do_relatorio(paginas: list[Pagina]) -> str:
    """'AAAA-MM' lido do título "Resumo Mensal <Mês> de <ano>" (confere a lista oficial)."""
    for pagina in paginas[:3]:
        achado = re.search(r"resumo mensal\s+([a-z]+)\s+de\s+(\d{4})", pagina.chave)
        if achado and achado.group(1) in MESES:
            return f"{achado.group(2)}-{MESES.index(achado.group(1)) + 1:02d}"
    raise TabelaNaoEncontrada("título 'Resumo Mensal <mês> de <ano>'")


def resumo_segmentos(paginas: list[Pagina]) -> list[dict]:
    for pagina in paginas[:3]:
        if "resumo mensal" not in pagina.chave:
            continue
        linhas = []
        texto = pagina.linhas
        for i, linha in enumerate(texto):
            chave = sem_acento(linha)
            for rotulo, segmento in SEGMENTOS_RESUMO.items():
                if chave.startswith(rotulo + " "):
                    numeros = linha[len(rotulo):].split()[:5]
                elif chave == rotulo and i > 0:
                    # Alguns PDFs (ex.: abr/2017) põem o rótulo um pouco abaixo da linha dos números.
                    numeros = texto[i - 1].split()[:5]
                else:
                    continue
                if len(numeros) == 5 and all(_NUMERO.match(n) for n in numeros):
                    linhas.append({"segmento": segmento, **dict(zip(COLUNAS_RESUMO, numeros))})
        if {r["segmento"] for r in linhas} == set(SEGMENTOS_RESUMO.values()):
            return linhas
    raise TabelaNaoEncontrada("resumo mensal por segmento (Autos, Com. Leves, A + B)")


# ---------- ranking por marca do mês ----------

_LINHA_MARCA = re.compile(rf"^{_RANK}\s+(.+?)\s+(\d[\d.]*)\s+(\d+(?:,\d+)?%)$")


def _linhas_de_marca(linhas: list[str], segmento: str) -> list[dict]:
    resultado = []
    for linha in linhas:
        achado = _LINHA_MARCA.match(linha)
        if achado:
            resultado.append({
                "segmento": segmento,
                "posicao": achado.group(1),
                "marca": achado.group(2).strip(),
                "quantidade": achado.group(3),
                "participacao": achado.group(4),
            })
    return resultado


def ranking_marcas(paginas: list[Pagina], acumulado: bool = False) -> list[dict]:
    """Ranking do mês, ou o acumulado do ano (nunca os de varejo/venda direta).

    A página tem automóveis à esquerda e comerciais leves à direita; abaixo, à esquerda,
    vem o bloco "Automóveis + Comerciais Leves".
    """
    for pagina in _caderno_de_leves(paginas):
        titulo = _titulo(pagina)
        if not titulo.startswith("ranking por marca") or ("acumulado" in titulo) != acumulado or "emplac" in titulo:
            continue
        meio = pagina.pagina.width / 2
        esquerda = pagina.texto_da_regiao(0, meio)
        direita = pagina.texto_da_regiao(meio, pagina.pagina.width)
        corte = next((i for i, l in enumerate(esquerda) if sem_acento(l).startswith("automoveis + comerciais")), None)
        if corte is None:
            raise TabelaNaoEncontrada("bloco 'Automóveis + Comerciais Leves' no ranking por marca")
        autos = _linhas_de_marca(esquerda[:corte], "automoveis")
        comerciais = _linhas_de_marca(direita, "comerciais_leves")
        leves = _linhas_de_marca(esquerda[corte:], "leves")
        if not autos and comerciais and leves:
            autos = _autos_pela_diferenca(leves, comerciais)
        if autos and comerciais and leves:
            return autos + comerciais + leves
    raise TabelaNaoEncontrada("ranking por marca " + ("acumulado" if acumulado else "do mês"))


def _autos_pela_diferenca(leves: list[dict], comerciais: list[dict]) -> list[dict]:
    """Automóveis = leves − comerciais leves, marca a marca.

    Caso real: em jan/2022 a tabela de automóveis foi colada como imagem. A lista de
    comerciais leves vai até as marcas de 1 unidade (é completa), então a diferença é exata
    para toda marca do ranking de leves. A participação fica vazia (calculada no dbt).
    """
    if not comerciais or inteiro(comerciais[-1]["quantidade"]) > 5:
        return []  # lista de comerciais cortada: a diferença não seria exata
    por_marca = {c["marca"]: inteiro(c["quantidade"]) for c in comerciais}
    autos = []
    for linha in leves:
        quantidade = inteiro(linha["quantidade"]) - por_marca.get(linha["marca"], 0)
        if quantidade > 0:
            autos.append({"segmento": "automoveis", "marca": linha["marca"], "quantidade": quantidade})
    autos.sort(key=lambda a: -a["quantidade"])
    return [
        {"segmento": "automoveis", "posicao": str(i), "marca": a["marca"], "quantidade": f"{a['quantidade']:,}".replace(",", "."), "participacao": None}
        for i, a in enumerate(autos, 1)
    ]


# ---------- modelos por categoria (páginas "Modelos mais emplacados acumulado até ...") ----------

_IGNORAR = re.compile(
    r"^(ed\.|informativo|sao paulo|www\.|modelos mais emplacados|modelo\b|part\.|\(?[a-e]\)|variacao|"
    r"(\d{4}\s*)+$|((jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)\w*\s*)+(acumulado)?$|\d+$)"
)
_SEGMENTO_TITULO = {"automoveis": "automoveis", "comerciais leves": "comerciais_leves"}


def _letras_dobradas(linha: str) -> bool:
    """Cabeçalho em negrito "impresso duas vezes" (jan/2022): 'DDeezz JJaann AAccuummuullaaddoo'."""
    letras = linha.replace(" ", "")
    return len(letras) >= 6 and len(letras) % 2 == 0 and all(letras[i] == letras[i + 1] for i in range(0, len(letras), 2))


def _eh_categoria(chave: str, linha: str) -> bool:
    return (not _IGNORAR.match(chave) and re.search(r"[a-z]", chave) is not None
            and not re.search(r"\d", chave) and not _letras_dobradas(linha))


def _separar_linha_de_modelo(linha: str) -> dict | None:
    """'3º FORD/KA SEDAN 0,00 0,00 = 5 0,01%' → posição, modelo e as três colunas de quantidade.

    Lida da direita: participação, acumulado, mês atual e mês anterior. Símbolos soltos entre
    as colunas (os relatórios recentes trazem '=') são ignorados; o resto é o nome do modelo.
    """
    achado = re.match(rf"^{_RANK}\s+(.*)$", linha)
    if not achado:
        return None
    partes = achado.group(2).split()
    if not partes or not _PERCENTUAL.match(partes[-1]):
        return None
    participacao = partes.pop()
    numeros = []
    while partes and len(numeros) < 3:
        token = partes.pop()
        if _NUMERO.match(token):
            numeros.append(token)
        elif re.fullmatch(r"[=▲▼↑↓+\-]+", token):
            continue
        else:
            partes.append(token)
            break
    if len(numeros) < 3 or not partes:
        return None
    acumulado, mes_atual, mes_anterior = numeros
    return {
        "posicao": achado.group(1),
        "modelo": " ".join(partes),
        "mes_anterior": mes_anterior,
        "mes_atual": mes_atual,
        "acumulado_ano": acumulado,
        "participacao": participacao,
    }


def modelos_por_categoria(paginas: list[Pagina]) -> list[dict]:
    resultado = []
    segmento = "automoveis"
    categoria = None
    for pagina in _caderno_de_leves(paginas):
        if not _titulo(pagina).startswith("modelos mais emplacados acumulado"):
            continue
        for linha in pagina.linhas:
            chave = sem_acento(linha)
            if chave in _SEGMENTO_TITULO:
                segmento = _SEGMENTO_TITULO[chave]
                continue
            if chave.startswith("total "):
                continue
            modelo = _separar_linha_de_modelo(linha)
            if modelo:
                if categoria is None:
                    raise TabelaNaoEncontrada(f"categoria antes do modelo {modelo['modelo']} (página {pagina.numero})")
                resultado.append({"segmento": segmento, "categoria": categoria, **modelo})
                continue
            if _eh_categoria(chave, linha):
                categoria = linha
    if not resultado:
        raise TabelaNaoEncontrada("modelos mais emplacados por categoria")
    return resultado


def totais_por_categoria(paginas: list[Pagina]) -> list[dict]:
    """Linhas 'Total' de cada categoria, quando o relatório traz (servem só para conferência)."""
    totais = []
    categoria = None
    for pagina in _caderno_de_leves(paginas):
        if not _titulo(pagina).startswith("modelos mais emplacados acumulado"):
            continue
        for linha in pagina.linhas:
            chave = sem_acento(linha)
            if _separar_linha_de_modelo(linha) or chave in _SEGMENTO_TITULO:
                continue
            if chave.startswith("total "):
                numeros = [t for t in linha.split()[1:] if _NUMERO.match(t)]
                if categoria and len(numeros) >= 3:
                    totais.append({"categoria": categoria, "mes_anterior": numeros[0], "mes_atual": numeros[1], "acumulado_ano": numeros[2]})
                continue
            if _eh_categoria(chave, linha):
                categoria = linha
    return totais


# ---------- canal: varejo × venda direta (pizzas vetoriais, dez/2024 em diante) ----------

SEGMENTOS_CANAL = ["automoveis", "comerciais_leves", "leves"]
_ROTULO_PCT = re.compile(r"^\d{1,3}(?:[.,]\d+)?%$")


def _ponto_no_poligono(x: float, y: float, poligono: list[tuple[float, float]]) -> bool:
    dentro = False
    for (x1, y1), (x2, y2) in zip(poligono, poligono[1:] + poligono[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            dentro = not dentro
    return dentro


def _eh_azul_escuro(cor) -> bool:
    """A fatia de venda direta é azul-escura; a de varejo, cinza."""
    if not isinstance(cor, (tuple, list)) or len(cor) != 3:
        return False
    r, _g, b = cor
    return b - r > 0.1


def canal_em_texto(paginas: list[Pagina]) -> list[dict] | None:
    """% de venda direta e de varejo do mês, quando a pizza é vetorial (rótulos em texto).

    Cada rótulo fica dentro da sua fatia, então a cor da fatia sob o rótulo diz o canal.
    Devolve None quando a página existe mas a pizza é imagem (relatórios até nov/2024):
    esses meses vêm da extração única guardada em dados/canal_pizzas_imagem.csv.
    """
    for pagina in _caderno_de_leves(paginas):
        titulo = _titulo(pagina)
        if not titulo.startswith("participacao de venda direta e venda varejo"):
            continue
        fatias = [c for c in pagina.pagina.curves if c.get("fill") and c.get("pts")]
        if not fatias:
            return None
        rotulos = []
        for palavra in pagina.pagina.extract_words():
            if not _ROTULO_PCT.match(palavra["text"]):
                continue
            x, y = (palavra["x0"] + palavra["x1"]) / 2, (palavra["top"] + palavra["bottom"]) / 2
            cores = [c.get("non_stroking_color") for c in fatias if _ponto_no_poligono(x, y, c["pts"])]
            if len(cores) != 1:
                raise TabelaNaoEncontrada(f"fatia sob o rótulo {palavra['text']} (página {pagina.numero})")
            rotulos.append((y, palavra["text"], "venda_direta" if _eh_azul_escuro(cores[0]) else "varejo"))
        rotulos.sort()
        if len(rotulos) != 6:
            raise TabelaNaoEncontrada(f"6 rótulos de % no canal (achados {len(rotulos)}, página {pagina.numero})")
        linhas = []
        for segmento, par in zip(SEGMENTOS_CANAL, [rotulos[0:2], rotulos[2:4], rotulos[4:6]]):
            por_canal = {canal: texto.rstrip("%").replace(",", ".") for _y, texto, canal in par}
            if set(por_canal) != {"venda_direta", "varejo"}:
                raise TabelaNaoEncontrada(f"um rótulo de cada canal em {segmento} (página {pagina.numero})")
            linhas.append({"segmento": segmento, "venda_direta_pct": por_canal["venda_direta"], "varejo_pct": por_canal["varejo"]})
        return linhas
    raise TabelaNaoEncontrada("página 'Participação de venda direta e venda varejo' do mês")
