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

```sql anual
select
    cast(ano as integer)                                        as ano,
    emplacamentos / 1e6                                         as milhoes,
    case when ano_parcial then 'Ano em andamento' else 'Ano completo' end as situacao
from veiculos.anual
where segmento = 'leves'
order by ano
```

Emplacamentos de automóveis e comerciais leves novos no Brasil, desde 2003. Fonte: Fenabrave. Dados até <Value data={resumo} column=ultimo_mes_txt />

<BigValue data={resumo} value=emplacamentos_ultimo_mes title="Último mês" fmt='#,##0' comparison=variacao_ultimo_mes comparisonFmt=pct1 comparisonTitle="vs. ano anterior" />
<BigValue data={resumo} value=emplacamentos_acumulado_ano title="Acumulado do ano" fmt='#,##0' comparison=variacao_acumulado_ano comparisonFmt=pct1 comparisonTitle="vs. ano anterior" />
<BigValue data={resumo} value=venda_direta_ultimo_mes title="Venda direta no mês" fmt=pct1 />
<BigValue data={resumo} value=participacao_marca_lider title={`${resumo[0]?.marca_lider_ultimo_mes ?? 'Marca líder'} no mês`} fmt=pct1 />

<BarChart
    data={anual}
    x=ano
    xFmt='0'
    y=milhoes
    series=situacao
    sort=false
    yFmt='#,##0.0" mi"'
    title="Emplacamentos por ano"
    subtitle="Recorde em 2012; quedas na recessão de 2015–2016 e na pandemia"
    colorPalette={['#1d4e89', '#9bb7d9']}
/>
