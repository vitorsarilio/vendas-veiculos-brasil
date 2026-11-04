---
title: Mercado
sidebar_position: 1
---

```sql meses_crescente
select strftime(mes_referencia, '%Y-%m') as mes, strftime(mes_referencia, '%m/%Y') as mes_nome
from veiculos.mensal where segmento = 'leves' order by mes
```

<PeriodoSlider data={meses_crescente} />

<ButtonGroup name=segmento>
    <ButtonGroupItem valueLabel="Leves" value="leves" default />
    <ButtonGroupItem valueLabel="Automóveis" value="automoveis" />
    <ButtonGroupItem valueLabel="Comerciais leves" value="comerciais_leves" />
</ButtonGroup>

```sql no_periodo
-- Meses entre "De" e "Até" (inclusive), em todos os segmentos
select * from veiculos.mensal
where strftime(mes_referencia, '%Y-%m') between '${inputs.inicio.value}' and '${inputs.fim.value}'
```

```sql anual_filtrado
-- Cada ano soma só os meses do período; a variação compara com os mesmos meses do ano anterior
select
    cast(ano as integer)                    as ano,
    sum(emplacamentos)                      as emplacamentos,
    sum(emplacamentos) / sum(emplacamentos_mesmo_mes_ano_anterior) - 1 as variacao
from ${no_periodo}
where segmento = '${inputs.segmento}'
group by ano
having count(emplacamentos_mesmo_mes_ano_anterior) = count(*)
order by ano
```

```sql mensal_filtrado
select mes_referencia + interval 12 hour as mes, 'Emplacamentos no mês' as serie, emplacamentos as valor
from ${no_periodo}
where segmento = '${inputs.segmento}'
union all
select mes_referencia + interval 12 hour, 'Média móvel de 12 meses', media_movel_12m
from ${no_periodo}
where segmento = '${inputs.segmento}' and media_movel_12m is not null
order by mes, serie
```

```sql anual
select
    cast(ano as integer)                    as ano,
    ano_parcial,
    emplacamentos,
    variacao_ano_anterior_pct / 100         as variacao
from veiculos.anual
where segmento = 'leves'
order by ano
```

```sql pico_e_vale
select
    (select ano from ${anual} where not ano_parcial order by emplacamentos desc limit 1) as ano_pico,
    (select emplacamentos from ${anual} where not ano_parcial order by emplacamentos desc limit 1) as pico,
    (select emplacamentos from ${anual} where ano = 2016) as em_2016,
    (select emplacamentos from ${anual} where ano = 2016)
        / (select emplacamentos from ${anual} where not ano_parcial order by emplacamentos desc limit 1) - 1 as queda_ate_2016,
    1 - (select emplacamentos from ${anual} where ano = 2016)
        / (select emplacamentos from ${anual} where not ano_parcial order by emplacamentos desc limit 1) as queda
```

```sql variacao_anual
select ano, variacao,
    case when variacao >= 0 then 'Alta' else 'Queda' end as sentido
from ${anual_filtrado}
where variacao is not null
order by ano
```

```sql segmentos_anual
select
    cast(ano as integer)        as ano,
    case segmento when 'automoveis' then 'Automóveis' else 'Comerciais leves' end as segmento,
    sum(emplacamentos)          as emplacamentos
from ${no_periodo}
where segmento <> 'leves'
group by all
order by ano, segmento
```

```sql sazonalidade
select
    cast(mes_do_ano as integer) as mes_do_ano,
    ['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez'][cast(mes_do_ano as integer)] as mes,
    indice_sazonal,
    indice_minimo,
    indice_maximo
from veiculos.sazonalidade
where segmento = '${inputs.segmento}'
order by mes_do_ano
```

```sql meses_extremos
select
    (select mes from ${sazonalidade} order by indice_sazonal desc limit 1) as mes_forte,
    (select indice_sazonal - 1 from ${sazonalidade} order by indice_sazonal desc limit 1) as acima,
    (select mes from ${sazonalidade} order by indice_sazonal limit 1) as mes_fraco,
    (select 1 - indice_sazonal from ${sazonalidade} order by indice_sazonal limit 1) as abaixo
```

## Crises e recuperação

Depois do pico de <Value data={pico_e_vale} column=ano_pico fmt='0' /> o mercado encolheu <Value data={pico_e_vale} column=queda fmt=pct0 /> até 2016 e voltou a cair na pandemia.

<BarChart
    data={variacao_anual}
    x=ano
    xFmt='0'
    y=variacao
    series=sentido
    sort=false
    yFmt=pct0
    title="Variação sobre o ano anterior"
    seriesColors={{'Alta': 'positive', 'Queda': 'negative'}}
/>

<LineChart
    data={mensal_filtrado}
    x=mes
    y=valor
    series=serie
    yFmt='#,##0'
    title="Emplacamentos por mês e média de 12 meses"
    seriesColors={{'Emplacamentos no mês': 'base-content-muted', 'Média móvel de 12 meses': 'accent'}}
    lineWidth=2.5
    chartAreaHeight=260
/>

## Automóveis e comerciais leves

<BarChart
    data={segmentos_anual}
    x=ano
    xFmt='0'
    y=emplacamentos
    series=segmento
    sort=false
    yFmt='#,##0'
    title="Emplacamentos por segmento"
    subtitle="Comerciais leves = picapes e furgões"
/>

## Sazonalidade

Em um ano típico, <Value data={meses_extremos} column=mes_forte /> fica <Value data={meses_extremos} column=acima fmt=pct0 /> acima do mês médio e <Value data={meses_extremos} column=mes_fraco /> fica <Value data={meses_extremos} column=abaixo fmt=pct0 /> abaixo.

<BarChart
    data={sazonalidade}
    x=mes
    y=indice_sazonal
    sort=false
    yFmt='#,##0.00'
    title="Peso de cada mês (1,00 = mês médio)"
    seriesOptions={{itemStyle: {borderRadius: [5, 5, 0, 0]}}}
/>
