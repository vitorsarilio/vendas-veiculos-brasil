"""Tudo o que muda quando a fonte muda fica aqui."""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DIR_RAW = RAIZ / "data" / "raw"
# Cópia local dos PDFs (e cache do GitHub Actions). Nunca versionada nem redistribuída.
DIR_PDFS = RAIZ / "data" / "pdfs"

# Lista oficial dos relatórios: o portal chama este serviço com "ano=AAAA" e recebe o nome
# real de cada arquivo. Os nomes não seguem um padrão fixo (2_2003_01_2.pdf, 6_2012_12_2.pdf,
# 2019_11_01.pdf, 2025_01_02.pdf), então não dá para montar a URL a partir da data.
URL_LISTA = "https://www.fenabrave.org.br/portalv2/api/Emplacamentos"
URL_ARQUIVO = "https://www.fenabrave.org.br/portal/files/{link}"

PRIMEIRO_ANO = 2003  # primeira edição do "Informativo - Emplacamentos" (fev/2003, dados de jan/2003)

USER_AGENT = "vendas-veiculos-brasil/1.0 (+https://github.com/vitorsarilio/vendas-veiculos-brasil)"
PAUSA_ENTRE_DOWNLOADS_S = 2  # gentileza com o servidor da Fenabrave

# Os relatórios mais recentes podem ser republicados com correção: sempre baixados de novo.
MESES_REBAIXADOS = 2

# Erros conhecidos da lista oficial: mês → arquivo certo. Conferido abrindo o PDF.
# abr/2005: a lista aponta para 3_2005_05_2.pdf, que é o relatório de maio.
CORRECOES_DA_LISTA = {"2005-04": "3_2005_04_2.pdf"}

# Meses publicados só numa edição resumida (10 páginas): têm o resumo e as marcas, mas não a
# tabela completa de modelos nem a página de varejo × venda direta. Procurado em todos os
# nomes alternativos do portal (2_2003_10_1.pdf, 2003_10_2.pdf, 3_2005_03_1.pdf etc.).
MESES_RESUMIDOS = {"2003-10", "2005-03"}

# % de venda direta dos meses em que a pizza do relatório é imagem (jan/2003 → out/2024).
# Extração única (OCR dos rótulos + conferência pela geometria da fatia), feita com
# scripts/recuperar_canal_imagens.py. Os relatórios antigos não mudam, então não se refaz.
ARQUIVO_CANAL_IMAGEM = Path(__file__).resolve().parent / "dados" / "canal_pizzas_imagem.csv"

# Faixa plausível para o total mensal de leves (automóveis + comerciais leves), em unidades.
# Folga larga em volta dos extremos da série (abr/2020, pandemia: 51 mil).
FAIXA_LEVES_MES = (30_000, 450_000)

# Meses publicados sem texto, reconstruídos dos relatórios vizinhos (ver reconstrucao.py).
MESES_RECONSTRUIDOS = {"2023-09": "publicado como impressão em PDF, sem texto"}

# Revisões da Fenabrave acima de 2% já conferidas: o relatório seguinte corrigiu o mês.
# fev/2022: o relatório de mar/2022 traz 100.006 automóveis (eram 97.590), +2,5%.
# A série usa o número publicado no relatório do próprio mês; a revisão fica registrada aqui.
REVISOES_CONHECIDAS = {"2022-02"}
