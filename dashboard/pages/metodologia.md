---
title: Metodologia
sidebar_position: 5
---

## Fonte

**Fenabrave** (Federação Nacional da Distribuição de Veículos Automotores), relatório mensal *Informativo – Emplacamentos*, com dados do Renavam/Senatran. Um PDF por mês desde janeiro de 2003, publicado no início do mês seguinte em [fenabrave.org.br](https://www.fenabrave.org.br/portalv2/Conteudo/Emplacamentos).

O projeto lê os PDFs, publica só números agregados e cita a fonte. Os PDFs não são redistribuídos.

## Definições

- **Emplacamento**: primeiro registro do veículo novo. É a medida de venda ao cliente final usada pelo setor.
- **Leves**: automóveis + comerciais leves. Comerciais leves são picapes e furgões; caminhões, ônibus e motos ficam de fora.
- **Varejo × venda direta**: a venda direta é faturada pela montadora direto para locadoras, frotistas, produtores rurais, taxistas, PcD e governo. O resto é varejo.
- **Atacado** (montadora → concessionária) não é medido pela Fenabrave, e sim pela Anfavea, e não entra aqui.
- **Origem da marca**: país de origem da marca, não o da fábrica.

## Como os dados são lidos

Toda semana um robô (GitHub Actions) baixa os relatórios novos, lê as tabelas de todos os PDFs de novo e confere os números antes de atualizar o painel. Se alguma conferência falha, nada é publicado e o painel continua com os dados anteriores. As conferências:

- automóveis + comerciais leves = total de leves, em todo mês;
- a soma das marcas e dos modelos nunca passa do total;
- o mês anterior de cada relatório bate com o relatório anterior (revisões de até 2%);
- a série não tem meses faltando desde jan/2003;
- varejo + venda direta = 100%.

## Casos especiais da fonte

| Mês | O que acontece | Como foi tratado |
|---|---|---|
| jan/2003 a jun/2024 | O gráfico de varejo × venda direta é uma imagem | Lido uma vez por reconhecimento de texto (OCR) e conferido de três formas: os dois percentuais somam 100%, o ângulo da fatia no gráfico confirma o valor, e o % de leves fecha com a média de automóveis e comerciais leves ponderada pelos volumes. Seis gráficos foram lidos à mão. |
| jul/2024 em diante | O gráfico passou a ter 1 casa decimal | Lido a cada atualização |
| out/2003 e mar/2005 | Só existe a edição resumida do relatório | Sem modelos e sem canal nesses meses |
| abr/2005 | A lista oficial aponta para o arquivo de maio | Usado o arquivo certo |
| set/2023 | O PDF não tem texto (foi "impresso" como imagem) | Reconstruído com os relatórios de agosto e outubro |
| jan/2022 | A tabela de marcas de automóveis é uma imagem | Automóveis = total de leves − comerciais leves, marca a marca |
| fev/2022 | O relatório seguinte corrigiu o mês em +2,5% | A série usa o número publicado no próprio mês |

## Limitações

- **Marcas**: a Fenabrave lista só as ~20 maiores de cada mês; o resto aparece como "Outras".
- **Modelos**: cada categoria lista os mais emplacados, então o total anual de um modelo é um piso.
- **Canais em unidades** são estimativas: percentual publicado × total do mês.
- **Sem dados por estado**: o relatório só traz as cinco regiões, em percentual.

Código, testes e documentação: [github.com/vitorsarilio/vendas-veiculos-brasil](https://github.com/vitorsarilio/vendas-veiculos-brasil).
