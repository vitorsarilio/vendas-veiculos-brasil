---
title: Marcas
sidebar_position: 3
---

<!--
  Filtros gerais (período, segmento, origem e marca) valem para o comparativo mês a mês e
  para o ranking do período. O ranking do mês tem o seu próprio seletor de mês.
  Os textos de destaque usam a série inteira de leves.
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

```sql meses
select
    strftime(mes_referencia, '%Y-%m')   as mes,
    strftime(mes_referencia, '%m/%Y')   as mes_nome
from veiculos.marcas_mensal
group by all
order by mes desc
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
-- Todas as marcas (e "Outras") no segmento e período; a participação é sobre o total do
-- segmento, então não muda quando se filtra a origem ou a marca
select
    cast(ano as integer)    as ano,
    marca,
    pais_origem,
    origem,
    eh_outras,
    emplacamentos
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

```sql ranking_mes
-- Todas as marcas do ranking no mês escolhido, com o mesmo mês do ano anterior
with mes as (
    select *
    from veiculos.marcas_mensal
    where segmento = '${inputs.segmento}'
      and strftime(mes_referencia, '%Y-%m') = '${inputs.mes.value}'
      and origem in ${inputs.origem.value}
      and marca in ${inputs.marca.value}
),
ano_anterior as (
    select marca, emplacamentos
    from veiculos.marcas_mensal
    where segmento = '${inputs.segmento}'
      and strftime(mes_referencia + interval 1 year, '%Y-%m') = '${inputs.mes.value}'
)
select
    cast(m.posicao as integer)                  as posicao,
    m.marca,
    m.pais_origem,
    m.emplacamentos,
    m.participacao_pct / 100                    as participacao,
    a.emplacamentos                             as mesmo_mes_ano_anterior,
    m.emplacamentos / a.emplacamentos - 1       as variacao
from mes as m
left join ano_anterior as a using (marca)
order by m.posicao
```

```sql escolhidas
select distinct marca from veiculos.marcas_mensal where marca in ${inputs.comparar.value}
```

```sql comparativo
-- Marcas escolhidas em "Comparar marcas"; sem escolha, as 5 maiores do período no filtro
with maiores as (select marca from ${ranking} order by posicao limit 5),
lista as (
    select marca from ${escolhidas}
    union all
    select marca from maiores where (select count(*) from ${escolhidas}) = 0
)
select
    mes_referencia + interval 12 hour   as mes,
    marca,
    emplacamentos,
    participacao_pct / 100              as participacao
from veiculos.marcas_mensal
where segmento = '${inputs.segmento}'
  and cast(ano as integer) between ${inputs.ano_inicio.value} and ${inputs.ano_fim.value}
  and marca in (select marca from lista)
order by mes, marca
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

<BigValue data={resumo_filtro} value=emplacamentos title="Emplacamentos das marcas no período" fmt='#,##0' />
<BigValue data={resumo_filtro} value=participacao title="Participação no segmento" fmt=pct1 />
<BigValue data={resumo_filtro} value=marcas title="Marcas" fmt='#,##0' />

## Ranking do mês

<Dropdown data={meses} name=mes value=mes label=mes_nome title="Mês" />

<DataTable data={ranking_mes} rows=25 search=true>
    <Column id=posicao title="#" />
    <Column id=marca title="Marca" />
    <Column id=pais_origem title="País de origem" />
    <Column id=emplacamentos title="Emplacamentos" fmt='#,##0' />
    <Column id=participacao title="Participação" fmt=pct1 />
    <Column id=mesmo_mes_ano_anterior title="Mesmo mês do ano anterior" fmt='#,##0' />
    <Column id=variacao title="Variação" fmt=pct0 contentType=delta />
</DataTable>

## Mês a mês

Escolha as marcas para comparar. Com a opção "As 5 maiores do período", aparecem as 5 maiores do período e do filtro acima.

<Dropdown data={opcoes_marca} name=comparar value=marca title="Comparar marcas" multiple=true defaultValue={['5 maiores']}>
    <DropdownOption value="5 maiores" valueLabel="As 5 maiores do período" />
</Dropdown>

<LineChart
    data={comparativo}
    x=mes
    y=emplacamentos
    series=marca
    yFmt='#,##0'
    title="Emplacamentos por mês"
/>

<LineChart
    data={comparativo}
    x=mes
    y=participacao
    series=marca
    yFmt=pct0
    title="Participação no segmento, por mês"
/>

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
