---
title: Modelos
sidebar_position: 4
---

<!--
  Filtros: o período começa nos últimos 12 meses; os demais aceitam vários valores e
  começam com tudo marcado. As consultas partem de `base`: com o canal "Todos",
  as tabelas por categoria; com um canal, as listas daquele canal (veiculos.modelos_canal).
-->

```sql meses_crescente
select strftime(mes_referencia, '%Y-%m') as mes, strftime(mes_referencia, '%m/%Y') as mes_nome
from veiculos.mensal where segmento = 'leves' order by mes
```

```sql opcoes_segmento
select distinct
    segmento,
    case segmento when 'automoveis' then 'Automóveis' else 'Comerciais leves' end as nome
from veiculos.modelos
order by nome
```

```sql opcoes_carroceria
-- Com as listas por canal: modelos que nunca aparecem nas tabelas por categoria ficam "Não classificado"
select distinct carroceria from veiculos.modelos
union
select distinct carroceria from veiculos.modelos_canal
order by carroceria
```

```sql opcoes_categoria
select distinct categoria from veiculos.modelos
union
select distinct categoria from veiculos.modelos_canal
order by categoria
```

```sql opcoes_marca
select marca, sum(total) as total
from (
    select marca, sum(emplacamentos) as total from veiculos.modelos group by marca
    union all
    select marca, 0 from veiculos.modelos_canal group by marca
)
group by marca
order by total desc, marca
```

```sql opcoes_origem
select distinct origem from veiculos.modelos
union
select distinct origem from veiculos.modelos_canal
order by origem
```

```sql inicio_padrao
-- Últimos 12 meses
select strftime(max(mes_referencia) - interval 11 month, '%Y-%m') as mes
from veiculos.mensal where segmento = 'leves'
```

```sql periodo
-- Períodos de mais de 3 anos viram médias anuais no gráfico de linha
select
    date_diff('month', strptime('${inputs.inicio.value}', '%Y-%m'), strptime('${inputs.fim.value}', '%Y-%m')) + 1 as meses,
    date_diff('month', strptime('${inputs.inicio.value}', '%Y-%m'), strptime('${inputs.fim.value}', '%Y-%m')) + 1 > 36 as anual
```

```sql opcoes_modelo
select modelo, sum(total) as total
from (
    select modelo_completo as modelo, sum(emplacamentos) as total from veiculos.modelos group by all
    union all
    select modelo_completo, 0 from veiculos.modelos_canal group by all
)
group by modelo
order by total desc, modelo
```

```sql base
-- Canal "Todos": as tabelas por categoria. Varejo ou venda direta: as listas do canal
select mes_referencia, ano, segmento, marca, pais_origem, origem, modelo_completo, categoria, carroceria, emplacamentos
from veiculos.modelos_mensal
where '${inputs.canal}' = 'todos'
union all
select mes_referencia, ano, segmento, marca, pais_origem, origem, modelo_completo, categoria, carroceria, emplacamentos
from veiculos.modelos_canal
where canal = '${inputs.canal}'
```

<PeriodoSlider data={meses_crescente} padrao={inicio_padrao[0]?.mes} />

<ButtonGroup name=canal>
    <ButtonGroupItem valueLabel="Todos os canais" value="todos" default />
    <ButtonGroupItem valueLabel="Varejo" value="varejo" />
    <ButtonGroupItem valueLabel="Venda direta" value="venda_direta" />
</ButtonGroup>
<Dropdown data={opcoes_segmento} name=segmento value=segmento label=nome title="Segmento" multiple=true selectAllByDefault=true />
<Dropdown data={opcoes_carroceria} name=carroceria value=carroceria title="Carroceria" multiple=true selectAllByDefault=true />
<Dropdown data={opcoes_categoria} name=categoria value=categoria title="Categoria" multiple=true selectAllByDefault=true />
<Dropdown data={opcoes_marca} name=marca value=marca title="Marca" multiple=true selectAllByDefault=true />
<Dropdown data={opcoes_origem} name=origem value=origem title="Origem" multiple=true selectAllByDefault=true />

```sql filtros
-- Todos os filtros, menos o período
select
    cast(ano as integer)        as ano,
    segmento,
    marca,
    modelo_completo,
    categoria,
    carroceria,
    mes_referencia,
    emplacamentos
from ${base}
where segmento in ${inputs.segmento.value}
  and carroceria in ${inputs.carroceria.value}
  and categoria in ${inputs.categoria.value}
  and marca in ${inputs.marca.value}
  and origem in ${inputs.origem.value}
```

```sql filtrado
select * from ${filtros}
where strftime(mes_referencia, '%Y-%m') between '${inputs.inicio.value}' and '${inputs.fim.value}'
```

```sql ranking
-- A variação compara com os mesmos meses um ano antes e só aparece em períodos de até 12 meses
with atual as (
    select
        modelo_completo                             as modelo,
        arg_max(categoria, emplacamentos)           as categoria,
        arg_max(carroceria, emplacamentos)          as carroceria,
        sum(emplacamentos)                          as emplacamentos
    from ${filtrado}
    group by modelo_completo
),
anterior as (
    select modelo_completo as modelo, sum(emplacamentos) as emplacamentos
    from ${filtros}
    where strftime(mes_referencia + interval 1 year, '%Y-%m') between '${inputs.inicio.value}' and '${inputs.fim.value}'
    group by modelo_completo
)
select
    row_number() over (order by a.emplacamentos desc, a.modelo) as posicao,
    a.*,
    a.emplacamentos / sum(a.emplacamentos) over ()  as participacao,
    a.emplacamentos / case when (select meses from ${periodo}) <= 12 then p.emplacamentos end - 1 as variacao
from atual as a
left join anterior as p using (modelo)
order by posicao
```

```sql escolhidos
select distinct modelo from ${opcoes_modelo} where modelo in ${inputs.comparar.value}
```

```sql comparativo
-- Modelos escolhidos em "Comparar"; sem escolha, os 5 maiores do filtro.
-- Períodos longos: média mensal de cada ano, para o gráfico não virar um emaranhado.
with maiores as (select modelo from ${ranking} order by posicao limit 5),
lista as (
    select modelo from ${escolhidos}
    union all
    select modelo from maiores where (select count(*) from ${escolhidos}) = 0
),
pontos as (
    select
        case when (select anual from ${periodo}) then make_date(year(mes_referencia), 7, 1)
             else mes_referencia end + interval 12 hour as mes,
        mes_referencia
    from veiculos.mensal
    where segmento = 'leves'
      and strftime(mes_referencia, '%Y-%m') between '${inputs.inicio.value}' and '${inputs.fim.value}'
),
meses as (select mes, count(*) as meses from pontos group by mes)
select
    p.mes,
    b.modelo_completo                       as modelo,
    sum(b.emplacamentos) / max(m.meses)     as emplacamentos
from ${base} as b
join pontos as p using (mes_referencia)
join meses as m on m.mes = p.mes
where b.modelo_completo in (select modelo from lista)
group by all
order by p.mes, modelo
```

```sql carroceria_por_ano
select ano, carroceria, sum(emplacamentos) as emplacamentos
from ${filtros}
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
    from ${filtros}
    group by all
)
group by ano
order by ano desc
```

```sql suv
with s as (
    select cast(ano as integer) as ano, participacao_nos_leves_pct / 100 as p, ano_incompleto
    from veiculos.carroceria where carroceria = 'SUV'
)
select
    (select p from s where not ano_incompleto order by ano desc limit 1) as agora,
    (select p from s where not ano_incompleto order by ano desc limit 1) - (select p from s where ano = 2010) as desde_2010
```

## Ranking

<DataTable data={ranking} rows=20 search=true>
    <Column id=posicao title="#" />
    <Column id=modelo title="Modelo" />
    <Column id=categoria title="Categoria" />
    <Column id=carroceria title="Carroceria" />
    <Column id=emplacamentos title="Emplacamentos" fmt='#,##0' />
    <Column id=participacao title="Participação" fmt=pct1 />
    <Column id=variacao title="vs. ano anterior" fmt=pct0 contentType=delta />
</DataTable>

## Evolução

<Dropdown data={opcoes_modelo} name=comparar value=modelo title="Comparar" multiple=true defaultValue={['5 maiores']}>
    <DropdownOption value="5 maiores" valueLabel="5 maiores" />
</Dropdown>

<LineChart
    data={comparativo}
    x=mes
    y=emplacamentos
    series=modelo
    lineWidth=2.5
    chartAreaHeight=260
    yFmt='#,##0'
    title={periodo[0]?.anual ? 'Emplacamentos (média mensal do ano)' : 'Emplacamentos por mês'}
/>

## O avanço dos SUVs

<div class="kpis">

<BigValue titleClass="titulo-kpi" valueClass="valor-grande" data={suv} value=agora title="SUVs nos leves" fmt=pct0 comparison=desde_2010 comparisonFmt=pct0 comparisonTitle="pontos desde 2010" />

</div>

<BarChart
        data={carroceria_por_ano}
        x=ano
        xFmt='0'
        y=emplacamentos
        series=carroceria
        type=stacked100
        sort=false
        title="Participação de cada carroceria, desde 2003"
        seriesColors={{'SUV': 'accent', 'Hatch': 'primary', 'Sedã': '#7c4dde', 'Picape': '#0f9f9a', 'Perua': '#b9c0cc', 'Minivan': '#e0b44c', 'Furgão': '#8f99aa', 'Esportivo': '#5b6678'}}
    />

<DataTable data={lideres} rows=10 title="Mais emplacado de cada ano">
    <Column id=ano title="Ano" />
    <Column id=modelo title="Modelo" />
    <Column id=emplacamentos title="Emplacamentos" fmt='#,##0' />
</DataTable>

<Alert status="info">

A Fenabrave lista só os mais emplacados de cada categoria (ou de cada canal), então o total de um modelo é um piso. [Metodologia](/metodologia)

</Alert>
