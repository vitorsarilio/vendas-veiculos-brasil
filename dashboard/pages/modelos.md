---
title: Modelos
sidebar_position: 4
---

<!--
  Filtros: os anos são escolhidos em dois seletores (de/até); os demais aceitam vários
  valores e começam com tudo marcado. Todas as consultas abaixo partem de `filtrado`.
-->

```sql anos_crescente
select distinct cast(ano as integer) as ano from veiculos.modelos order by ano
```

```sql anos_decrescente
select distinct cast(ano as integer) as ano from veiculos.modelos order by ano desc
```

```sql opcoes_segmento
select distinct
    segmento,
    case segmento when 'automoveis' then 'Automóveis' else 'Comerciais leves' end as nome
from veiculos.modelos
order by nome
```

```sql opcoes_carroceria
select distinct carroceria from veiculos.modelos order by carroceria
```

```sql opcoes_categoria
select distinct categoria from veiculos.modelos order by categoria
```

```sql opcoes_marca
select marca, sum(emplacamentos) as total from veiculos.modelos group by marca order by total desc
```

```sql opcoes_origem
select distinct origem from veiculos.modelos order by origem
```

<Dropdown data={anos_crescente} name=ano_inicio value=ano title="De" />
<Dropdown data={anos_decrescente} name=ano_fim value=ano title="Até" />
<Dropdown data={opcoes_segmento} name=segmento value=segmento label=nome title="Segmento" multiple=true selectAllByDefault=true />
<Dropdown data={opcoes_carroceria} name=carroceria value=carroceria title="Carroceria" multiple=true selectAllByDefault=true />
<Dropdown data={opcoes_categoria} name=categoria value=categoria title="Categoria" multiple=true selectAllByDefault=true />
<Dropdown data={opcoes_marca} name=marca value=marca title="Marca" multiple=true selectAllByDefault=true />
<Dropdown data={opcoes_origem} name=origem value=origem title="Origem da marca" multiple=true selectAllByDefault=true />

```sql filtrado
select
    cast(ano as integer)        as ano,
    segmento,
    case segmento when 'automoveis' then 'Automóvel' else 'Comercial leve' end as segmento_nome,
    marca,
    pais_origem,
    origem,
    modelo_completo,
    categoria,
    carroceria,
    emplacamentos
from veiculos.modelos
where cast(ano as integer) between ${inputs.ano_inicio.value} and ${inputs.ano_fim.value}
  and segmento in ${inputs.segmento.value}
  and carroceria in ${inputs.carroceria.value}
  and categoria in ${inputs.categoria.value}
  and marca in ${inputs.marca.value}
  and origem in ${inputs.origem.value}
```

```sql resumo_filtro
select
    sum(emplacamentos)                  as emplacamentos,
    count(distinct modelo_completo)     as modelos,
    count(distinct marca)               as marcas
from ${filtrado}
```

```sql ranking
select
    row_number() over (order by sum(emplacamentos) desc, modelo_completo) as posicao,
    modelo_completo                                 as modelo,
    marca,
    arg_max(segmento_nome, emplacamentos)           as segmento,
    arg_max(categoria, emplacamentos)               as categoria,
    arg_max(carroceria, emplacamentos)              as carroceria,
    origem,
    sum(emplacamentos)                              as emplacamentos,
    sum(emplacamentos) / sum(sum(emplacamentos)) over () as participacao,
    cast(min(ano) as varchar) || case when min(ano) < max(ano) then '–' || cast(max(ano) as varchar) else '' end as anos
from ${filtrado}
group by modelo_completo, marca, origem
order by emplacamentos desc
```

```sql evolucao
-- Os 8 modelos com mais emplacamentos no filtro, ano a ano
with top as (select modelo from ${ranking} order by posicao limit 8)
select f.ano, f.modelo_completo as modelo, sum(f.emplacamentos) as emplacamentos
from ${filtrado} as f
join top as t on t.modelo = f.modelo_completo
group by all
order by f.ano, emplacamentos desc
```

```sql carroceria_por_ano
select ano, carroceria, sum(emplacamentos) as emplacamentos
from ${filtrado}
group by all
order by ano, carroceria
```

```sql lideres
select
    cast(ano as varchar)                        as ano,
    arg_max(modelo_completo, emplacamentos)     as modelo,
    max(emplacamentos)                          as emplacamentos
from (
    select ano, modelo_completo, sum(emplacamentos) as emplacamentos
    from ${filtrado}
    group by all
)
group by ano
order by ano
```

```sql suv
select
    (select participacao_nos_leves_pct / 100 from veiculos.carroceria where carroceria = 'SUV' and ano = 2010) as em_2010,
    (select participacao_nos_leves_pct / 100 from veiculos.carroceria where carroceria = 'SUV' and not ano_incompleto order by ano desc limit 1) as agora,
    (select cast(cast(ano as integer) as varchar) from veiculos.carroceria where carroceria = 'SUV' and not ano_incompleto order by ano desc limit 1) as ano_agora
```

<BigValue data={resumo_filtro} value=emplacamentos title="Emplacamentos no filtro" fmt='#,##0' />
<BigValue data={resumo_filtro} value=modelos title="Modelos" fmt='#,##0' />
<BigValue data={resumo_filtro} value=marcas title="Marcas" fmt='#,##0' />

## Todos os modelos

Todos os modelos listados pela Fenabrave no período e nos filtros escolhidos. Use a busca da tabela para achar um modelo pelo nome.

<DataTable data={ranking} rows=25 search=true>
    <Column id=posicao title="#" />
    <Column id=modelo title="Modelo" />
    <Column id=segmento title="Segmento" />
    <Column id=categoria title="Categoria" />
    <Column id=carroceria title="Carroceria" />
    <Column id=origem title="Origem" />
    <Column id=emplacamentos title="Emplacamentos" fmt='#,##0' />
    <Column id=participacao title="Participação" fmt=pct1 />
    <Column id=anos title="Anos listado" />
</DataTable>

<LineChart
    data={evolucao}
    x=ano
    xFmt='0'
    y=emplacamentos
    series=modelo
    yFmt='#,##0'
    title="Evolução dos 8 modelos mais emplacados no filtro"
    subtitle="Para comparar modelos específicos, escolha as marcas, a categoria ou a carroceria acima"
/>

## O avanço dos SUVs

Os SUVs eram <Value data={suv} column=em_2010 fmt=pct0 /> dos leves em 2010 e chegaram a **<Value data={suv} column=agora fmt=pct0 />** em <Value data={suv} column=ano_agora />, tomando espaço dos hatches e dos sedãs. As picapes, principalmente as pequenas (Strada, Saveiro, Montana), também cresceram. O gráfico abaixo segue os filtros: escolha uma marca para ver como ela mudou o seu portfólio.

<BarChart
    data={carroceria_por_ano}
    x=ano
    xFmt='0'
    y=emplacamentos
    series=carroceria
    type=stacked100
    sort=false
    title="Participação de cada carroceria"
    subtitle="Pela categoria da Fenabrave, dentro dos filtros escolhidos"
/>

<DataTable data={lideres} rows=30 title="Modelo mais emplacado de cada ano (no filtro)">
    <Column id=ano title="Ano" />
    <Column id=modelo title="Modelo" />
    <Column id=emplacamentos title="Emplacamentos" fmt='#,##0' />
</DataTable>

<Alert status="info">

A Fenabrave lista os modelos mais emplacados de cada categoria, não todos. Por isso, o total de um modelo no ano é um **piso**: se ele ficou fora da lista em algum mês, aquele mês não entra, e modelos de volume muito baixo podem nem aparecer. O ano mais recente ainda está em andamento, e 2003 e 2005 têm um mês sem a tabela de modelos.

</Alert>
