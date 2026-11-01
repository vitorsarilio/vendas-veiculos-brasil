# Relatórios de emplacamento da Fenabrave: o que existe em cada época

Reconhecimento feito em 01/11/2026, com 22 PDFs de amostra entre jan/2003 e set/2026.

## Como achar os arquivos

- **A URL não segue um padrão fixo.** Exemplos: `2_2003_01_2.pdf`, `6_2012_12_2.pdf`, `2017_06_2.pdf`, `2019_11_01.pdf`, `2025_01_02.pdf`.
- **Lista oficial:** `POST https://www.fenabrave.org.br/portalv2/api/Emplacamentos` com `ano=AAAA` devolve JSON com `data.blocos[]`. Cada item traz `data` (AAAA-MM-01), `link` (nome do arquivo) e `descricao` (flipbook).
- **Download:** `https://www.fenabrave.org.br/portal/files/<link>`.
- **Mês inexistente:** devolve 404 com página HTML de cerca de 5 kB. Validar sempre o início `%PDF-`.
- **Cobertura:** 286 itens, de jan/2003 a set/2026, sem lacunas. Jun/2019 aparece duas vezes (`2019_06_2.pdf` e `2_2019_06_2.pdf`, com os mesmos números); a ingestão fica com o de contador maior.
- **Erro da lista:** abr/2005 aponta para `3_2005_05_2.pdf`, que é o relatório de maio. O certo é `3_2005_04_2.pdf` (correção em `config.CORRECOES_DA_LISTA`; a qualidade confere o mês escrito em cada PDF).
- **Calendário:** o relatório do mês M sai no início de M+1. O de set/2026 é a edição de outubro.

## Estrutura (estável de 2003 a 2026; só muda a numeração das páginas)

O caderno de automóveis e comerciais leves sempre vem nas primeiras páginas:

| Conteúdo | Formato | Desde | Decisão |
|---|---|---|---|
| Resumo mensal por segmento (autos, comerciais leves, A+B, caminhões, ônibus, motos…): mês, mês anterior, acumulado, mesmo mês do ano anterior | tabela em texto | 2003 | **go** |
| Ranking por marca (autos e comerciais leves separados): quantidade e participação, lista completa | tabela em texto | 2003 | **go** |
| Ranking de modelos do mês (top N por segmento) | tabela em texto | 2003 | **go** |
| Modelos por subsegmento (entrada, hatch, sedã, SUV, picapes…): mês anterior, mês, acumulado do ano e participação, cerca de 150 a 180 modelos | tabela em texto | 2003 | **go**, permite responder sobre SUVs |
| Varejo × venda direta, em % (autos, comerciais leves, A+B, mês e acumulado) | **imagem** com % de 2 casas até jun/2024; **vetorial com texto** (1 casa) a partir de jul/2024 | 2003 | **go**, com extração única das imagens antigas |
| Modelos mais emplacados em venda direta e em varejo (top N, unidades) | tabela em texto | 2005 (a confirmar para 2003) | go opcional |
| Ranking por marca em varejo e em venda direta | gráfico de barras | – | no-go |
| Regiões (5 regiões, %) | gráfico com rótulos em texto | 2003 | opcional |
| UF | não existe | – | **no-go** |
| Mercado de eletrificados | tabela | recente (a confirmar desde quando) | bônus opcional |

## Problemas encontrados (leitura dos 285 relatórios, 01/11/2026)

| Mês | Problema | Tratamento |
|---|---|---|
| abr/2020 | Fonte sem mapa de caracteres: o texto sai como `(cid:NN)` | Deslocamento fixo de +29 (`(cid:36)` = "A") e tabela de acentos (`pdf.CID_ESPECIAIS`) |
| out/2003 e mar/2005 | Só existe a edição resumida (10 páginas), sem modelos nem varejo × venda direta | `config.MESES_RESUMIDOS`: entram resumo e marcas; modelos e canal ficam vazios nesses meses |
| set/2023 | "Impresso para PDF": as letras viraram desenho, nenhum caractere legível | Reconstruído dos vizinhos (`reconstrucao.py`): coluna "mês anterior" de out/2023 e diferença entre rankings acumulados |
| abr/2017 a fev/2018 (5 meses) | No resumo, o rótulo do segmento sai uma linha abaixo dos números | O leitor aceita os dois arranjos |
| jan/2022 | A tabela de marcas de automóveis foi colada como imagem | Automóveis = leves − comerciais leves, marca a marca (a lista de comerciais é completa) |
| dez/2024 em diante | As páginas de modelos não trazem a linha "Total" por categoria | A conferência por categoria só roda quando o total existe |

**Varejo × venda direta em imagem (jan/2003 a jun/2024).** Extração única com `scripts/recuperar_canal_imagens.py`, guardada em `ingestion/ingestao/dados/canal_pizzas_imagem.csv`:

- OCR dos rótulos (2 casas decimais) em 753 pizzas; 9 já tinham os rótulos em texto; 6 foram lidas olhando a imagem.
- O rótulo da venda direta é sempre o de baixo: a fatia escura começa às 3 horas e gira no sentido horário.
- Conferências: os dois rótulos somam 100,00%; o ângulo da fatia medido na imagem bate (até 5 p.p.); e o % de leves é a média de automóveis e comerciais leves ponderada pelos volumes, com erro máximo de 0,008 p.p. nos 256 meses.

A partir de jul/2024 a pizza é vetorial e o canal é lido a cada execução, pela cor da fatia sob cada rótulo (azul-escuro = venda direta). Esses rótulos têm só 1 casa decimal.

**Unidades por canal** = % × total do segmento. É uma aproximação: até ±0,005 p.p. de arredondamento nas imagens (algumas unidades) e ±0,05 p.p. a partir de jul/2024 (cerca de 100 unidades num mês de 200 mil).

## Termos

O site diz "© Fenabrave – Todos os direitos reservados", e os PDFs não trazem aviso sobre reprodução. O projeto publica só agregados derivados, cita a fonte e não redistribui os PDFs (o cache fica fora do git).

## Download a partir do GitHub Actions

Testado em 01/11/2026 (execução 41357315463): a lista oficial (2003 e 2026) e dois PDFs (2003 e 2026) baixaram normalmente de um runner `ubuntu-latest`. A automação semanal é viável.
