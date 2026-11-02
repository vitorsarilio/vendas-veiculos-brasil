---
title: Marcas
sidebar_position: 3
---

<!--
  Os textos de destaque usam a série inteira de leves; tabelas e gráficos seguem os filtros.
-->

```sql anos_crescente
select distinct cast(ano as integer) as ano from veiculos.marcas order by ano
```

```sql anos_decrescente
select distinct cast(ano as integer) as ano from veiculos.marcas order by ano desc
```

```sql opcoes_origem
select distinct origem from veiculos.marcas where not eh_outras order by origem
```

```sql opcoes_marca
-- Todos os segmentos: algumas marcas só aparecem no ranking de comerciais leves
select marca, sum(emplacamentos) filter (where segmento = 'leves') as total
from veiculos.marcas
where not eh_outras
group by marca
order by total desc nulls last, marca
```

<Dropdown data={anos_crescente} name=ano_inicio value=ano title="De" />
<Dropdown data={anos_decrescente} name=ano_fim value=ano title="Até" />
<ButtonGroup name=segmento title="Segmento">
    <ButtonGroupItem valueLabel="Leves" value="leves" default />
    <ButtonGroupItem valueLabel="Automóveis" value="automoveis" />
    <ButtonGroupItem valueLabel="Comerciais leves" value="comerciais_leves" />
</ButtonGroup>
<Dropdown data={opcoes_origem} name=origem value=origem title="Origem da marca" multiple=true selectAllByDefault=true />
<Dropdown data={opcoes_marca} name=marca value=marca title="Marca" multiple=true selectAllByDefault=true />

```sql no_periodo
-- Todas as marcas (e "Outras") no segmento e período escolhidos; a participação é sobre o
-- total do segmento, então não muda quando se filtra a origem ou a marca
select
    cast(ano as integer)    as ano,
    marca,
    pais_origem,
    origem,
    eh_outras,
    emplacamentos,
    emplacamentos / sum(emplacamentos) over (partition by ano) as participacao
from veiculos.marcas
where segmento = '${inputs.segmento}'
  and cast(ano as integer) between ${inputs.ano_inicio.value} and ${inputs.ano_fim.value}
```

```sql filtrado
select * from ${no_periodo}
where not eh_outras
  and origem in ${inputs.origem.value}
  and marca in ${inputs.marca.value}
```

```sql total_periodo
select sum(emplacamentos) as total from ${no_periodo}
```

```sql ranking
select
    row_number() over (order by sum(f.emplacamentos) desc, f.marca) as posicao,
    f.marca,
    f.pais_origem,
    f.origem,
    sum(f.emplacamentos)                                    as emplacamentos,
    sum(f.emplacamentos) / max(t.total)                     as participacao,
    count(distinct f.ano)                                   as anos_no_ranking,
    cast(min(f.ano) as varchar) || case when min(f.ano) < max(f.ano) then '–' || cast(max(f.ano) as varchar) else '' end as anos
from ${filtrado} as f
cross join ${total_periodo} as t
group by f.marca, f.pais_origem, f.origem
order by emplacamentos desc
```

```sql resumo_filtro
select
    sum(emplacamentos)          as emplacamentos,
    sum(participacao)           as participacao,
    count(*)                    as marcas
from ${ranking}
```

```sql evolucao
-- As 8 marcas com mais emplacamentos no filtro, ano a ano
with top as (select marca from ${ranking} order by posicao limit 8)
select f.ano, f.marca, f.participacao
from ${filtrado} as f
join top as t using (marca)
order by f.ano, f.participacao desc
```

```sql origem_por_ano
select ano, origem, sum(emplacamentos) as emplacamentos
from ${no_periodo}
group by all
order by ano, origem
```

```sql quatro_grandes
select
    cast(ano as integer) as ano,
    sum(participacao_pct) filter (where marca in ('Fiat', 'Volkswagen', 'Chevrolet', 'Ford')) / 100 as quatro_grandes
from veiculos.marcas
where segmento = 'leves'
group by ano
```

```sql china
select cast(ano as integer) as ano, participacao_pct / 100 as participacao
from veiculos.origem
where segmento = 'leves' and origem = 'China'
```

```sql destaques
select
    (select quatro_grandes from ${quatro_grandes} where ano = 2003) as em_2003,
    (select quatro_grandes from ${quatro_grandes} order by ano desc limit 1) as agora,
    (select ano from ${quatro_grandes} order by ano desc limit 1) as ano_atual,
    (select participacao from ${china} order by ano desc limit 1) as china_agora,
    (select participacao from ${china} where ano = 2020) as china_2020
```

<BigValue data={resumo_filtro} value=emplacamentos title="Emplacamentos das marcas escolhidas" fmt='#,##0' />
<BigValue data={resumo_filtro} value=participacao title="Participação no segmento" fmt=pct1 />
<BigValue data={resumo_filtro} value=marcas title="Marcas" fmt='#,##0' />

## Ranking no período

Todas as marcas que apareceram no ranking da Fenabrave no período e no segmento escolhidos. A participação é sobre o total do segmento.

<DataTable data={ranking} rows=25 search=true>
    <Column id=posicao title="#" />
    <Column id=marca title="Marca" />
    <Column id=pais_origem title="País de origem" />
    <Column id=emplacamentos title="Emplacamentos" fmt='#,##0' />
    <Column id=participacao title="Participação" fmt=pct1 />
    <Column id=anos title="Anos no ranking" />
</DataTable>

<LineChart
    data={evolucao}
    x=ano
    xFmt='0'
    y=participacao
    series=marca
    yFmt=pct0
    title="Participação das 8 maiores marcas do filtro, ano a ano"
    subtitle="Para comparar marcas específicas, escolha-as no filtro de marca"
/>

## A queda das quatro grandes

Fiat, Volkswagen, Chevrolet (GM) e Ford tinham **<Value data={destaques} column=em_2003 fmt=pct0 />** do mercado de leves em 2003. Em <Value data={destaques} column=ano_atual fmt='0' />, as quatro somam <Value data={destaques} column=agora fmt=pct0 />. A Ford deixou de fabricar carros no Brasil em 2021 e hoje vende poucos modelos importados.

## A chegada das chinesas

As marcas chinesas tinham <Value data={destaques} column=china_2020 fmt=pct1 /> do mercado de leves em 2020. Com BYD, GWM, Chery, GAC e Geely, já chegam a **<Value data={destaques} column=china_agora fmt=pct1 />** no ano mais recente. A origem considerada é a da marca, não a da fábrica: um Jeep feito em Pernambuco conta como Estados Unidos.

<BarChart
    data={origem_por_ano}
    x=ano
    xFmt='0'
    y=emplacamentos
    series=origem
    type=stacked100
    sort=false
    title="Participação por origem da marca"
    subtitle="No segmento e período escolhidos. Não classificado = marcas fora do top 20 de cada mês"
/>

<Alert status="info">

A Fenabrave lista as ~20 maiores marcas de cada mês por segmento; o restante entra em "Outras", que não aparece no ranking. Nomes diferentes da mesma marca foram unificados: GM e Chevrolet; Chery, Caoa Chery e Rely; Chana e Changan; Great Wall e GWM.

</Alert>
