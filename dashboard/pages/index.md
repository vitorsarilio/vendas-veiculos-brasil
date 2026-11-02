---
title: Vendas de veículos leves no Brasil
---

<!--
  Datas: o navegador converte datas para o fuso local (UTC−3), o que mostraria o dia
  anterior. Por isso as datas de texto são formatadas no SQL, e os meses dos gráficos
  ficam ao meio-dia do dia 1.
-->

```sql resumo
select
    *,
    strftime(ultimo_mes, '%m/%Y')               as ultimo_mes_txt,
    strftime(primeiro_mes, '%m/%Y')             as primeiro_mes_txt,
    cast(cast(ano_recorde as integer) as varchar) as ano_recorde_txt,
    emplacamentos_ano_recorde / 1e6             as recorde_milhoes,
    variacao_ultimo_mes_pct / 100               as variacao_ultimo_mes,
    variacao_acumulado_ano_pct / 100            as variacao_acumulado_ano,
    venda_direta_ultimo_mes_pct / 100           as venda_direta_ultimo_mes,
    participacao_marca_lider_pct / 100          as participacao_marca_lider
from veiculos.resumo
```

```sql mensal
select mes_referencia + interval 12 hour as mes, 'Emplacamentos no mês' as serie, emplacamentos as valor
from veiculos.mensal where segmento = 'leves'
union all
select mes_referencia + interval 12 hour, 'Média móvel de 12 meses', media_movel_12m
from veiculos.mensal where segmento = 'leves' and media_movel_12m is not null
order by mes, serie
```

```sql anual
select
    cast(ano as integer)                                        as ano,
    emplacamentos / 1e6                                         as milhoes,
    case when ano_parcial then 'Ano em andamento' else 'Ano completo' end as situacao
from veiculos.anual
where segmento = 'leves'
order by ano
```

Painel sobre os **emplacamentos de automóveis e comerciais leves novos** no Brasil, mês a mês, desde janeiro de 2003. Emplacamento é o registro do veículo novo no Renavam: é a medida oficial de venda ao consumidor final. Os dados vêm dos relatórios mensais da **Fenabrave**, e o painel é atualizado automaticamente toda semana.

<BigValue data={resumo} value=emplacamentos_ultimo_mes title="Emplacamentos no último mês" fmt='#,##0' comparison=variacao_ultimo_mes comparisonFmt=pct1 comparisonTitle="vs. mesmo mês do ano anterior" />
<BigValue data={resumo} value=emplacamentos_acumulado_ano title="Acumulado do ano" fmt='#,##0' comparison=variacao_acumulado_ano comparisonFmt=pct1 comparisonTitle="vs. mesmos meses do ano anterior" />
<BigValue data={resumo} value=venda_direta_ultimo_mes title="Venda direta no último mês" fmt=pct1 />
<BigValue data={resumo} value=participacao_marca_lider title="Participação da marca líder" fmt=pct1 />

<Alert status="info">

Último relatório: **<Value data={resumo} column=ultimo_mes_txt />**. Marca líder no mês: **<Value data={resumo} column=marca_lider_ultimo_mes />**; modelo mais emplacado: **<Value data={resumo} column=modelo_lider_ultimo_mes />** (<Value data={resumo} column=emplacamentos_modelo_lider fmt='#,##0' /> unidades). "Leves" = automóveis + comerciais leves (picapes e furgões); caminhões, ônibus e motos ficam de fora.

</Alert>

## Quanto o Brasil emplaca por ano?

O recorde da série é **<Value data={resumo} column=ano_recorde_txt />**, com <Value data={resumo} column=recorde_milhoes fmt='#,##0.00' /> milhões de veículos leves. Depois vieram a recessão de 2015–2016 e a pandemia de 2020.

<BarChart
    data={anual}
    x=ano
    xFmt='0'
    y=milhoes
    series=situacao
    sort=false
    yFmt='#,##0.0" mi"'
    title="Emplacamentos de veículos leves por ano"
    colorPalette={['#1d4e89', '#9bb7d9']}
/>

<LineChart
    data={mensal}
    x=mes
    y=valor
    series=serie
    yFmt='#,##0'
    title="Emplacamentos por mês"
    subtitle="Com a média móvel de 12 meses, que tira o efeito da sazonalidade"
/>

## Explore as outras perguntas

- [**Mercado**](/mercado): crises, recuperação, sazonalidade e a divisão entre automóveis e comerciais leves.
- [**Canais**](/canais): quanto vai para o varejo e quanto para venda direta (locadoras, frotistas, PcD, governo).
- [**Marcas**](/marcas): a perda de espaço das quatro grandes e a chegada das chinesas.
- [**Modelos**](/modelos): os mais emplacados de cada ano e o avanço dos SUVs.
- [**Metodologia**](/metodologia): fonte, como os PDFs são lidos, definições e limitações.
