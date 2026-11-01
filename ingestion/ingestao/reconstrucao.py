"""Reconstrução de um mês cujo PDF não tem texto, a partir dos relatórios vizinhos.

Caso real: set/2023 foi publicado "impresso para PDF", com as letras viradas desenho.
Os números do mês continuam nos vizinhos, sem estimativa:
- segmentos e modelos: a coluna "mês anterior" do relatório seguinte;
- marcas: acumulado até o mês = acumulado do seguinte − mês do seguinte; o mês sai da
  diferença para o acumulado do relatório anterior (as revisões da Fenabrave entram aqui,
  na casa das dezenas de unidades por marca). Marca fora de algum dos três rankings
  (cauda do top 20) fica de fora e cai em "Outras" no dbt, como nos outros meses;
- canal: as pizzas ainda são imagem e entram pela extração única (canal_pizzas_imagem.csv).
"""

from ingestao import tabelas
from ingestao.pdf import abrir, inteiro


def _formatar(numero: int) -> str:
    return f"{numero:,}".replace(",", ".")


def _percentual(parte: int, total: int) -> str:
    return f"{parte / total * 100:.2f}%".replace(".", ",") if total else "0,00%"


def reconstruir_mes(mes: str, caminho_anterior, caminho_seguinte) -> dict:
    resultado = {"mes": mes, "mes_no_pdf": mes, "erros": [], "fenabrave_canal": None}
    doc_ant, pags_ant = abrir(caminho_anterior)
    doc_seg, pags_seg = abrir(caminho_seguinte)
    try:
        seg_ant = {s["segmento"]: s for s in tabelas.resumo_segmentos(pags_ant)}
        seg_seg = {s["segmento"]: s for s in tabelas.resumo_segmentos(pags_seg)}
        segmentos, total_mes = [], {}
        for nome, s in seg_seg.items():
            mes_atual = inteiro(s["mes_anterior"])
            acumulado = inteiro(s["acumulado_ano"]) - inteiro(s["mes_atual"])
            # A Fenabrave revisa os meses já publicados em dezenas de unidades; acima de
            # 0,5% de diferença, algo foi lido errado.
            pelos_acumulados = acumulado - inteiro(seg_ant[nome]["acumulado_ano"])
            if abs(pelos_acumulados - mes_atual) > mes_atual * 0.005:
                resultado["erros"].append(f"reconstrução: acumulados de {nome} dão {pelos_acumulados}, o mês diz {mes_atual}")
            total_mes[nome] = mes_atual
            segmentos.append({
                "segmento": nome,
                "mes_atual": _formatar(mes_atual),
                "mes_anterior": seg_ant[nome]["mes_atual"],
                "acumulado_ano": _formatar(acumulado),
                "mesmo_mes_ano_anterior": None,
                "acumulado_ano_anterior": None,
            })
        resultado["fenabrave_segmentos"] = segmentos

        def por_marca(linhas):
            return {(l["segmento"], l["marca"]): inteiro(l["quantidade"]) for l in linhas}

        acum_seg = por_marca(tabelas.ranking_marcas(pags_seg, acumulado=True))
        mes_seg = por_marca(tabelas.ranking_marcas(pags_seg))
        acum_ant = por_marca(tabelas.ranking_marcas(pags_ant, acumulado=True))
        marcas = []
        for chave in acum_seg.keys() & mes_seg.keys() & acum_ant.keys():
            quantidade = acum_seg[chave] - mes_seg[chave] - acum_ant[chave]
            if quantidade < 0:
                resultado["erros"].append(f"reconstrução: {chave} ficou negativa ({quantidade})")
                continue
            marcas.append({"segmento": chave[0], "marca": chave[1], "quantidade": quantidade})
        marcas.sort(key=lambda m: (m["segmento"], -m["quantidade"], m["marca"]))
        posicao = {}
        for m in marcas:
            posicao[m["segmento"]] = posicao.get(m["segmento"], 0) + 1
            m["posicao"] = str(posicao[m["segmento"]])
            m["participacao"] = _percentual(m["quantidade"], total_mes[m["segmento"]])
            m["quantidade"] = _formatar(m["quantidade"])
        resultado["fenabrave_marcas"] = marcas

        modelos = []
        for linha in tabelas.modelos_por_categoria(pags_seg):
            modelos.append({
                "segmento": linha["segmento"],
                "categoria": linha["categoria"],
                "posicao": None,
                "modelo": linha["modelo"],
                "mes_anterior": None,
                "mes_atual": linha["mes_anterior"],
                "acumulado_ano": _formatar(inteiro(linha["acumulado_ano"]) - inteiro(linha["mes_atual"])),
                "participacao": None,
            })
        resultado["fenabrave_modelos"] = modelos
        resultado["totais_modelos"] = []
    except Exception as erro:  # noqa: BLE001 - vira item do relatório de qualidade
        resultado["erros"].append(f"reconstrução: {type(erro).__name__}: {erro}")
    finally:
        doc_ant.close()
        doc_seg.close()
    return resultado
