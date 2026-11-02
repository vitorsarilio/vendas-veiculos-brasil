---
title: Mercado
sidebar_position: 1
---

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
        / (select emplacamentos from ${anual} where not ano_parcial order by emplacamentos desc limit 1) - 1 as queda_ate_2016
```

```sql variacao_anual
select ano, variacao,
    case when variacao >= 0 then 'Alta' else 'Queda' end as sentido
from ${anual}
where variacao is not null
order by ano
```

```sql segmentos_anual
select
    cast(ano as integer)        as ano,
    case segmento when 'automoveis' then 'Automóveis' else 'Comerciais leves' end as segmento,
    emplacamentos
from veiculos.anual
where segmento <> 'leves'
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
where segmento = 'leves'
order by mes_do_ano
```

```sql meses_extremos
select
    (select mes from ${sazonalidade} order by indice_sazonal desc limit 1) as mes_forte,
    (select indice_sazonal - 1 from ${sazonalidade} order by indice_sazonal desc limit 1) as acima,
    (select mes from ${sazonalidade} order by indice_sazonal limit 1) as mes_fraco,
    (select 1 - indice_sazonal from ${sazonalidade} order by indice_sazonal limit 1) as abaixo
```

## O tamanho do mercado desde 2003

O mercado de leves mais que dobrou entre 2003 e o pico de **<Value data={pico_e_vale} column=ano_pico fmt='0' />** (<Value data={pico_e_vale} column=pico fmt='#,##0' /> emplacamentos), puxado por crédito farto e redução de IPI. Na recessão, encolheu <Value data={pico_e_vale} column=queda_ate_2016 fmt=pct0 /> até 2016. A pandemia derrubou 2020, e a recuperação seguinte foi travada pela falta de semicondutores.

<BarChart
    data={variacao_anual}
    x=ano
    xFmt='0'
    y=variacao
    series=sentido
    sort=false
    yFmt=pct0
    title="Variação sobre o ano anterior"
    subtitle="No ano em andamento, a comparação é com os mesmos meses do ano anterior"
    colorPalette={['#2f855a', '#c53030']}
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

<BarChart
    data={segmentos_anual}
    x=ano
    xFmt='0'
    y=emplacamentos
    series=segmento
    type=stacked100
    sort=false
    title="Participação de cada segmento"
/>

## Sazonalidade

Dezembro concentra compras de fim de ano e de frotas: em um ano típico, **<Value data={meses_extremos} column=mes_forte />** fica <Value data={meses_extremos} column=acima fmt=pct0 /> acima do mês médio. **<Value data={meses_extremos} column=mes_fraco />**, mais curto e com férias e Carnaval, fica <Value data={meses_extremos} column=abaixo fmt=pct0 /> abaixo.

<BarChart
    data={sazonalidade}
    x=mes
    y=indice_sazonal
    sort=false
    yFmt='#,##0.00'
    title="Peso de cada mês (1,00 = mês médio do ano)"
    subtitle="Mediana dos anos completos desde 2003"
/>

<DataTable data={sazonalidade} rows=12>
    <Column id=mes title="Mês" />
    <Column id=indice_sazonal title="Índice típico" fmt='#,##0.00' />
    <Column id=indice_minimo title="Menor" fmt='#,##0.00' />
    <Column id=indice_maximo title="Maior" fmt='#,##0.00' />
</DataTable>
