---
title: Marcas
sidebar_position: 3
---

<!--
  Filtros gerais (período, segmento, canal, origem e marca) valem para o comparativo mês a
  mês e para o ranking do período. O ranking do mês tem o seu próprio seletor de mês.
  Com um canal escolhido, cada marca é a soma dos seus modelos listados naquele canal
  (veiculos.modelos_canal). Os textos de destaque usam a série inteira de leves.
-->

```sql meses_crescente
select strftime(mes_referencia, '%Y-%m') as mes, strftime(mes_referencia, '%m/%Y') as mes_nome
from veiculos.mensal where segmento = 'leves' order by mes
```

```sql meses_decrescente
select strftime(mes_referencia, '%Y-%m') as mes, strftime(mes_referencia, '%m/%Y') as mes_nome
from veiculos.mensal where segmento = 'leves' order by mes desc
```

```sql opcoes_origem
select distinct origem from veiculos.marcas where not eh_outras
union
select distinct origem from veiculos.modelos_canal
order by origem
```

```sql opcoes_marca
-- Todos os segmentos e canais: algumas marcas só aparecem no ranking de comerciais leves
-- ou nas listas por canal
select marca, sum(total) as total
from (
    select marca, sum(emplacamentos) filter (where segmento = 'leves') as total
    from veiculos.marcas where not eh_outras group by marca
    union all
    select marca, 0 from veiculos.modelos_canal group by marca
)
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

<Dropdown data={meses_crescente} name=inicio value=mes label=mes_nome order=mes title="De (mês/ano)" />
<Dropdown data={meses_decrescente} name=fim value=mes label=mes_nome order="mes desc" title="Até (mês/ano)" />
<ButtonGroup name=segmento title="Segmento">
    <ButtonGroupItem valueLabel="Leves" value="leves" default />
    <ButtonGroupItem valueLabel="Automóveis" value="automoveis" />
    <ButtonGroupItem valueLabel="Comerciais leves" value="comerciais_leves" />
</ButtonGroup>
<ButtonGroup name=canal title="Canal">
    <ButtonGroupItem valueLabel="Todos" value="todos" default />
    <ButtonGroupItem valueLabel="Varejo" value="varejo" />
    <ButtonGroupItem valueLabel="Venda direta" value="venda_direta" />
</ButtonGroup>
<Dropdown data={opcoes_origem} name=origem value=origem title="Origem da marca" multiple=true selectAllByDefault=true />
<Dropdown data={opcoes_marca} name=marca value=marca title="Marca" multiple=true selectAllByDefault=true />

```sql base_mensal
-- Marcas de cada mês no segmento e canal escolhidos. "Todos": o ranking de marcas da
-- Fenabrave. Um canal: a soma dos modelos da marca listados naquele canal.
select mes_referencia, cast(ano as integer) as ano, marca, pais_origem, origem, emplacamentos
from veiculos.marcas_mensal
where '${inputs.canal}' = 'todos' and segmento = '${inputs.segmento}'
union all
select mes_referencia, cast(ano as integer), marca, pais_origem, origem, sum(emplacamentos)
from veiculos.modelos_canal
where canal = '${inputs.canal}'
  and ('${inputs.segmento}' = 'leves' or segmento = '${inputs.segmento}')
group by all
```

```sql total_mensal
-- Total do segmento (ou do canal) em cada mês, incluindo as marcas fora das listas.
-- Com um canal, só os meses que têm as listas por canal.
select
    mes_referencia,
    cast(ano as integer) as ano,
    case '${inputs.canal}'
        when 'varejo' then emplacamentos_varejo
        when 'venda_direta' then emplacamentos_venda_direta
        else emplacamentos
    end as total
from veiculos.mensal
where segmento = '${inputs.segmento}'
  and ('${inputs.canal}' = 'todos'
       or mes_referencia in (select distinct mes_referencia from veiculos.modelos_canal))
```

```sql no_periodo
-- Marcas em cada mês entre "De" e "Até"
select * from ${base_mensal}
where strftime(mes_referencia, '%Y-%m') between '${inputs.inicio.value}' and '${inputs.fim.value}'
```

```sql filtrado
select * from ${no_periodo}
where origem in ${inputs.origem.value}
  and marca in ${inputs.marca.value}
```

```sql total_por_ano
-- A participação é sobre o total do segmento (ou do canal), então não muda quando se
-- filtra a origem ou a marca
select ano, sum(total) as total
from ${total_mensal}
where strftime(mes_referencia, '%Y-%m') between '${inputs.inicio.value}' and '${inputs.fim.value}'
group by ano
```

```sql total_periodo
select sum(total) as total from ${total_por_ano}
```

```sql ranking
select
    row_number() over (order by sum(f.emplacamentos) desc, f.marca) as posicao,
    f.marca,
    f.pais_origem,
    f.origem,
    sum(f.emplacamentos)                                    as emplacamentos,
    sum(f.emplacamentos) / max(t.total)                     as participacao,
    count(distinct f.mes_referencia)                        as meses
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
-- Todas as marcas do mês escolhido, com o mesmo mês do ano anterior
with mes as (
    select
        b.*,
        b.emplacamentos / t.total                               as participacao,
        row_number() over (order by b.emplacamentos desc, b.marca) as posicao
    from ${base_mensal} as b
    join ${total_mensal} as t using (mes_referencia)
    where strftime(b.mes_referencia, '%Y-%m') = '${inputs.mes.value}'
),
ano_anterior as (
    select marca, emplacamentos
    from ${base_mensal}
    where strftime(mes_referencia + interval 1 year, '%Y-%m') = '${inputs.mes.value}'
)
select
    m.posicao,
    m.marca,
    m.pais_origem,
    m.emplacamentos,
    m.participacao,
    a.emplacamentos                             as mesmo_mes_ano_anterior,
    m.emplacamentos / a.emplacamentos - 1       as variacao
from mes as m
left join ano_anterior as a using (marca)
where m.origem in ${inputs.origem.value}
  and m.marca in ${inputs.marca.value}
order by m.posicao
```

```sql escolhidas
select distinct marca from ${opcoes_marca} where marca in ${inputs.comparar.value}
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
    n.mes_referencia + interval 12 hour     as mes,
    n.marca,
    n.emplacamentos,
    n.emplacamentos / t.total               as participacao
from ${no_periodo} as n
join ${total_mensal} as t using (mes_referencia)
where n.marca in (select marca from lista)
order by mes, n.marca
```

```sql origem_por_ano
-- As marcas fora das listas entram como "Não classificado"
with marcas as (
    select ano, origem, sum(emplacamentos) as emplacamentos
    from ${no_periodo}
    group by all
),
fora_do_ranking as (
    select t.ano, 'Não classificado' as origem, t.total - coalesce(sum(m.emplacamentos), 0) as emplacamentos
    from ${total_por_ano} as t
    left join marcas as m using (ano)
    group by t.ano, t.total
)
select ano, origem, sum(emplacamentos) as emplacamentos
from (select * from marcas union all select * from fora_do_ranking)
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
<BigValue data={resumo_filtro} value=participacao title="Participação no segmento (ou no canal)" fmt=pct1 />
<BigValue data={resumo_filtro} value=marcas title="Marcas" fmt='#,##0' />

## Ranking do mês

<Dropdown data={meses} name=mes value=mes label=mes_nome order="mes desc" title="Mês" />

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

Todas as marcas que apareceram no ranking da Fenabrave no período e no segmento escolhidos. A participação é sobre o total do segmento ou, com um canal escolhido, sobre o total do canal.

<DataTable data={ranking} rows=25 search=true>
    <Column id=posicao title="#" />
    <Column id=marca title="Marca" />
    <Column id=pais_origem title="País de origem" />
    <Column id=emplacamentos title="Emplacamentos" fmt='#,##0' />
    <Column id=participacao title="Participação" fmt=pct1 />
    <Column id=meses title="Meses no ranking" fmt='#,##0' />
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

**Filtro de canal:** a Fenabrave não publica as marcas com unidades por canal, só os ~50 automóveis e ~40 comerciais leves mais emplacados em cada canal no mês. Com "Varejo" ou "Venda direta", cada marca é a soma dos seus modelos dessas listas: um piso, que cobre de 88% a 100% do canal. As marcas pequenas quase somem, e out/2003, mar/2005 e set/2023 ficam de fora (não têm as listas). A Fenabrave não mede o atacado (venda da montadora para a concessionária), que é dado da Anfavea.

</Alert>
