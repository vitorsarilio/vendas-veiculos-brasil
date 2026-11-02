---
title: Modelos
sidebar_position: 4
---

```sql anos
select distinct cast(cast(ano as integer) as varchar) as ano
from veiculos.modelos_top
order by ano desc
```

```sql top_do_ano
select
    cast(posicao_leves as integer) as posicao,
    modelo_completo             as modelo,
    case segmento when 'automoveis' then 'Automóvel' else 'Comercial leve' end as segmento,
    categoria,
    emplacamentos
from veiculos.modelos_top
where cast(cast(ano as integer) as varchar) = '${inputs.ano.value}' and posicao_leves <= 10
order by posicao_leves
```

```sql lideres
-- O modelo mais emplacado de cada ano
select
    cast(cast(ano as integer) as varchar)    as ano,
    modelo_completo         as modelo,
    emplacamentos,
    ano_incompleto
from veiculos.modelos_top
where posicao_leves = 1
order by ano
```

```sql carroceria
select
    cast(ano as integer)        as ano,
    carroceria,
    sum(emplacamentos)          as emplacamentos
from veiculos.carroceria
group by all
order by ano, carroceria
```

```sql suv
select
    (select participacao_nos_leves_pct / 100 from veiculos.carroceria where carroceria = 'SUV' and ano = 2010) as em_2010,
    (select participacao_nos_leves_pct / 100 from veiculos.carroceria where carroceria = 'SUV' and not ano_incompleto order by ano desc limit 1) as agora,
    (select cast(cast(ano as integer) as varchar) from veiculos.carroceria where carroceria = 'SUV' and not ano_incompleto order by ano desc limit 1) as ano_agora
```

## O avanço dos SUVs

Os SUVs eram <Value data={suv} column=em_2010 fmt=pct0 /> dos leves em 2010 e chegaram a **<Value data={suv} column=agora fmt=pct0 />** em <Value data={suv} column=ano_agora />, tomando espaço dos hatches e dos sedãs. As picapes, principalmente as pequenas (Strada, Saveiro, Montana), também cresceram.

<BarChart
    data={carroceria}
    x=ano
    xFmt='0'
    y=emplacamentos
    series=carroceria
    type=stacked100
    sort=false
    title="Participação de cada carroceria nos leves"
    subtitle="Pela categoria da Fenabrave; soma das listas de modelos de cada categoria"
/>

## Os mais emplacados de cada ano

<Dropdown data={anos} name=ano value=ano title="Ano" />

<DataTable data={top_do_ano} rows=10>
    <Column id=posicao title="#" />
    <Column id=modelo title="Modelo" />
    <Column id=segmento title="Segmento" />
    <Column id=categoria title="Categoria" />
    <Column id=emplacamentos title="Emplacamentos" fmt='#,##0' />
</DataTable>

<DataTable data={lideres} rows=30 title="Líder de cada ano">
    <Column id=ano title="Ano" />
    <Column id=modelo title="Modelo mais emplacado" />
    <Column id=emplacamentos title="Emplacamentos" fmt='#,##0' />
</DataTable>

<Alert status="info">

A Fenabrave lista os modelos mais emplacados de cada categoria, não todos. Por isso, o total de um modelo no ano é um **piso**: se ele ficou fora da lista em algum mês, aquele mês não entra. O ano mais recente ainda está em andamento, e 2003 e 2005 têm um mês sem a tabela de modelos.

</Alert>
