---
title: Marcas
sidebar_position: 3
---

```sql marcas
select
    cast(ano as integer)        as ano,
    ano_parcial,
    marca,
    pais_origem,
    eh_outras,
    cast(posicao as integer) as posicao,
    emplacamentos,
    participacao_pct / 100      as participacao
from veiculos.marcas
where segmento = 'leves'
order by ano, emplacamentos desc
```

```sql quatro_grandes
select
    ano,
    sum(participacao) filter (where marca in ('Fiat', 'Volkswagen', 'Chevrolet', 'Ford'))  as quatro_grandes
from ${marcas}
group by ano
order by ano
```

```sql destaques
select
    (select quatro_grandes from ${quatro_grandes} where ano = 2003) as em_2003,
    (select quatro_grandes from ${quatro_grandes} order by ano desc limit 1) as agora,
    (select ano from ${quatro_grandes} order by ano desc limit 1) as ano_atual,
    (select participacao from ${origem} where origem = 'China' order by ano desc limit 1) as china_agora,
    (select participacao from ${origem} where origem = 'China' and ano = 2020) as china_2020
```

```sql principais
-- As 6 maiores do ano mais recente, mais a Ford; as demais somadas em "Demais marcas"
-- (8 séries: uma cor para cada)
with top as (
    select marca from ${marcas} where ano = (select max(ano) from ${marcas}) and posicao <= 6
    union
    select 'Ford'
)
select
    m.ano,
    case when t.marca is null then 'Demais marcas' else m.marca end as marca,
    sum(m.participacao) as participacao
from ${marcas} as m
left join top as t using (marca)
group by all
order by m.ano, participacao desc
```

```sql origem
select
    cast(ano as integer)        as ano,
    origem,
    participacao_pct / 100      as participacao
from veiculos.origem
where segmento = 'leves'
order by ano, origem
```

```sql ranking_atual
select
    posicao, marca, pais_origem, emplacamentos, participacao
from ${marcas}
where ano = (select max(ano) from ${marcas}) and not eh_outras
order by posicao
limit 20
```

## A queda das quatro grandes

Fiat, Volkswagen, Chevrolet (GM) e Ford tinham **<Value data={destaques} column=em_2003 fmt=pct0 />** do mercado de leves em 2003. Em <Value data={destaques} column=ano_atual fmt='0' />, as quatro somam <Value data={destaques} column=agora fmt=pct0 />. A Ford deixou de fabricar carros no Brasil em 2021 e hoje vende poucos modelos importados.

<LineChart
    data={principais}
    x=ano
    xFmt='0'
    y=participacao
    series=marca
    yFmt=pct0
    title="Participação das principais marcas nos leves"
    subtitle="As 6 maiores do ano mais recente, mais a Ford"
/>

## A chegada das chinesas

As marcas chinesas tinham <Value data={destaques} column=china_2020 fmt=pct1 /> do mercado em 2020. Com BYD, GWM, Chery, GAC e Geely, já chegam a **<Value data={destaques} column=china_agora fmt=pct1 />** no ano mais recente. A origem considerada é a da marca, não a da fábrica: um Jeep feito em Pernambuco conta como Estados Unidos.

<BarChart
    data={origem}
    x=ano
    xFmt='0'
    y=participacao
    series=origem
    type=stacked100
    sort=false
    title="Participação por origem da marca"
    subtitle="Não classificado = marcas fora do top 20 de cada mês, que a Fenabrave não detalha"
/>

## Ranking do ano mais recente

<DataTable data={ranking_atual} rows=20>
    <Column id=posicao title="#" />
    <Column id=marca title="Marca" />
    <Column id=pais_origem title="Origem" />
    <Column id=emplacamentos title="Emplacamentos" fmt='#,##0' />
    <Column id=participacao title="Participação" fmt=pct1 />
</DataTable>

<Alert status="info">

A Fenabrave lista as ~20 maiores marcas de cada mês; o restante entra em "Outras". Nomes diferentes da mesma marca foram unificados: GM e Chevrolet; Chery, Caoa Chery e Rely; Chana e Changan; Great Wall e GWM.

</Alert>
