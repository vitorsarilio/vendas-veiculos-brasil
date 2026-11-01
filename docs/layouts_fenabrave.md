# Relatórios de emplacamento da Fenabrave: o que existe em cada época

Reconhecimento feito em 01/11/2026, com 22 PDFs de amostra entre jan/2003 e set/2026.

## Como achar os arquivos

- **A URL não segue um padrão fixo.** Exemplos: `2_2003_01_2.pdf`, `6_2012_12_2.pdf`, `2017_06_2.pdf`, `2019_11_01.pdf`, `2025_01_02.pdf`.
- **Lista oficial:** `POST https://www.fenabrave.org.br/portalv2/api/Emplacamentos` com `ano=AAAA` devolve JSON com `data.blocos[]`. Cada item traz `data` (AAAA-MM-01), `link` (nome do arquivo) e `descricao` (flipbook).
- **Download:** `https://www.fenabrave.org.br/portal/files/<link>`.
- **Mês inexistente:** devolve 404 com página HTML de cerca de 5 kB. Validar sempre o início `%PDF-`.
- **Cobertura:** 286 itens, de jan/2003 a set/2026, sem lacunas. 2019 tem um mês repetido (13 itens); é preciso resolver a duplicata na ingestão.
- **Calendário:** o relatório do mês M sai no início de M+1. O de set/2026 é a edição de outubro.

## Estrutura (estável de 2003 a 2026; só muda a numeração das páginas)

O caderno de automóveis e comerciais leves sempre vem nas primeiras páginas:

| Conteúdo | Formato | Desde | Decisão |
|---|---|---|---|
| Resumo mensal por segmento (autos, comerciais leves, A+B, caminhões, ônibus, motos…): mês, mês anterior, acumulado, mesmo mês do ano anterior | tabela em texto | 2003 | **go** |
| Ranking por marca (autos e comerciais leves separados): quantidade e participação, lista completa | tabela em texto | 2003 | **go** |
| Ranking de modelos do mês (top N por segmento) | tabela em texto | 2003 | **go** |
| Modelos por subsegmento (entrada, hatch, sedã, SUV, picapes…): mês anterior, mês, acumulado do ano e participação, cerca de 150 a 180 modelos | tabela em texto | 2003 | **go**, permite responder sobre SUVs |
| Varejo × venda direta, em % (autos, comerciais leves, A+B, mês e acumulado) | **imagem** com % de 2 casas até nov/2024; **texto** a partir de dez/2024 | 2003 | **go**, com extração única das imagens antigas |
| Modelos mais emplacados em venda direta e em varejo (top N, unidades) | tabela em texto | 2005 (a confirmar para 2003) | go opcional |
| Ranking por marca em varejo e em venda direta | gráfico de barras | – | no-go |
| Regiões (5 regiões, %) | gráfico com rótulos em texto | 2003 | opcional |
| UF | não existe | – | **no-go** |
| Mercado de eletrificados | tabela | recente (a confirmar desde quando) | bônus opcional |

## Problemas encontrados

- **Fonte sem mapa de caracteres:** abr/2020 sai como `(cid:NN)`. O deslocamento é fixo (+29: `(cid:36)` = "A", `(cid:19)` = "0", `(cid:3)` = espaço); acentos precisam de uma pequena tabela. Varrer todos os 286 PDFs no Passo 2 para ver quantos têm o problema.
- **Varejo × direta antes de dez/2024 só existe como imagem.** Exemplo, dez/2012: autos 81,14% varejo / 18,86% direta. Os relatórios antigos não mudam, então a extração é feita uma vez, validada (soma = 100,00%; a cor escura é sempre "venda direta") e guardada como tabela fixa com a origem.
- **Unidades por canal** = % × total do segmento. São uma aproximação, com erro de poucas dezenas de unidades.

## Termos

O site diz "© Fenabrave – Todos os direitos reservados", e os PDFs não trazem aviso sobre reprodução. O projeto publica só agregados derivados, cita a fonte e não redistribui os PDFs (o cache fica fora do git).

## Download a partir do GitHub Actions

Testado em 01/11/2026 (execução 41357315463): a lista oficial (2003 e 2026) e dois PDFs (2003 e 2026) baixaram normalmente de um runner `ubuntu-latest`. A automação semanal é viável.
