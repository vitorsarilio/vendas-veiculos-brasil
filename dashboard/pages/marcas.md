---
title: Marcas
sidebar_position: 3
---

<!--
  Os filtros valem para a página toda. O período começa nos últimos 12 meses.
  Com um canal escolhido, cada marca é a soma dos seus modelos listados naquele canal
  (veiculos.modelos_canal). Os destaques do fim da página usam a série inteira de leves.
-->

```sql meses_crescente
select strftime(mes_referencia, '%Y-%m') as mes, strftime(mes_referencia, '%m/%Y') as mes_nome
from veiculos.mensal where segmento = 'leves' order by mes
```

```sql meses_decrescente
select strftime(mes_referencia, '%Y-%m') as mes, strftime(mes_referencia, '%m/%Y') as mes_nome
from veiculos.mensal where segmento = 'leves' order by mes desc
```

```sql inicio_padrao
-- Últimos 12 meses
select strftime(max(mes_referencia) - interval 11 month, '%Y-%m') as mes
from veiculos.mensal where segmento = 'leves'
```

```sql opcoes_origem
select distinct origem from veiculos.marcas where not eh_outras
union
select distinct origem from veiculos.modelos_canal
order by origem
```

```sql opcoes_marca
-- Algumas marcas só aparecem no ranking de comerciais leves ou nas listas por canal
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

<Dropdown data={meses_crescente} name=inicio value=mes label=mes_nome order=mes title="De" defaultValue={inicio_padrao[0]?.mes} />
<Dropdown data={meses_decrescente} name=fim value=mes label=mes_nome order="mes desc" title="Até" />
<ButtonGroup name=segmento>
    <ButtonGroupItem valueLabel="Leves" value="leves" default />
    <ButtonGroupItem valueLabel="Automóveis" value="automoveis" />
    <ButtonGroupItem valueLabel="Comerciais leves" value="comerciais_leves" />
</ButtonGroup>
<ButtonGroup name=canal>
    <ButtonGroupItem valueLabel="Todos os canais" value="todos" default />
    <ButtonGroupItem valueLabel="Varejo" value="varejo" />
    <ButtonGroupItem valueLabel="Venda direta" value="venda_direta" />
</ButtonGroup>
<Dropdown data={opcoes_origem} name=origem value=origem title="Origem" multiple=true selectAllByDefault=true />
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

```sql periodo
-- Períodos de mais de 3 anos viram médias anuais nos gráficos de linha
select
    date_diff('month', strptime('${inputs.inicio.value}', '%Y-%m'), strptime('${inputs.fim.value}', '%Y-%m')) + 1 as meses,
    date_diff('month', strptime('${inputs.inicio.value}', '%Y-%m'), strptime('${inputs.fim.value}', '%Y-%m')) + 1 > 36 as anual
```

```sql no_periodo
select * from ${base_mensal}
where strftime(mes_referencia, '%Y-%m') between '${inputs.inicio.value}' and '${inputs.fim.value}'
```

```sql total_por_ano
-- A participação é sobre o total do segmento (ou do canal): não muda com o filtro de origem ou marca
select ano, sum(total) as total
from ${total_mensal}
where strftime(mes_referencia, '%Y-%m') between '${inputs.inicio.value}' and '${inputs.fim.value}'
group by ano
```

```sql ranking
-- A posição é entre todas as marcas; a variação compara com os mesmos meses um ano antes
-- e só aparece em períodos de até 12 meses
with atual as (
    select marca, pais_origem, origem, sum(emplacamentos) as emplacamentos
    from ${no_periodo}
    group by all
),
anterior as (
    select marca, sum(emplacamentos) as emplacamentos
    from ${base_mensal}
    where strftime(mes_referencia + interval 1 year, '%Y-%m') between '${inputs.inicio.value}' and '${inputs.fim.value}'
    group by marca
),
posicoes as (
    select
        row_number() over (order by a.emplacamentos desc, a.marca) as posicao,
        a.*,
        a.emplacamentos / (select sum(total) from ${total_por_ano}) as participacao,
        case when (select meses from ${periodo}) <= 12 then p.emplacamentos end as anterior
    from atual as a
    left join anterior as p using (marca)
)
select *, emplacamentos / anterior - 1 as variacao
from posicoes
where origem in ${inputs.origem.value}
  and marca in ${inputs.marca.value}
order by posicao
```

```sql escolhidas
select distinct marca from ${opcoes_marca} where marca in ${inputs.comparar.value}
```

```sql comparativo
-- Marcas escolhidas em "Comparar"; sem escolha, as 5 maiores do filtro.
-- Períodos longos: média mensal de cada ano, para o gráfico não virar um emaranhado.
with maiores as (select marca from ${ranking} order by posicao limit 5),
lista as (
    select marca from ${escolhidas}
    union all
    select marca from maiores where (select count(*) from ${escolhidas}) = 0
),
pontos as (
    select
        case when (select anual from ${periodo}) then make_date(year(mes_referencia), 7, 1)
             else mes_referencia end + interval 12 hour as mes,
        mes_referencia,
        total
    from ${total_mensal}
    where strftime(mes_referencia, '%Y-%m') between '${inputs.inicio.value}' and '${inputs.fim.value}'
),
totais as (
    select mes, count(*) as meses, sum(total) as total from pontos group by mes
)
select
    p.mes,
    n.marca,
    sum(n.emplacamentos) / max(t.meses)     as emplacamentos,
    sum(n.emplacamentos) / max(t.total)     as participacao
from ${no_periodo} as n
join pontos as p using (mes_referencia)
join totais as t on t.mes = p.mes
where n.marca in (select marca from lista)
group by all
order by p.mes, n.marca
```

```sql origem_por_ano
-- Série inteira (ignora o período), no segmento e canal escolhidos.
-- As marcas fora das listas entram como "Outras marcas"
with marcas as (
    select ano, origem, sum(emplacamentos) as emplacamentos
    from ${base_mensal}
    group by all
),
fora_do_ranking as (
    select t.ano, 'Outras marcas' as origem, t.total - coalesce(sum(m.emplacamentos), 0) as emplacamentos
    from (select ano, sum(total) as total from ${total_mensal} group by ano) as t
    left join marcas as m using (ano)
    group by t.ano, t.total
)
select ano, case origem when 'Não classificado' then 'Outras marcas' else origem end as origem, sum(emplacamentos) as emplacamentos
from (select * from marcas union all select * from fora_do_ranking)
group by all
order by ano, origem
```

```sql destaques
with quatro as (
    select cast(ano as integer) as ano,
        sum(participacao_pct) filter (where marca in ('Fiat', 'Volkswagen', 'Chevrolet', 'Ford')) / 100 as p
    from veiculos.marcas where segmento = 'leves' group by ano
),
china as (
    select cast(ano as integer) as ano, participacao_pct / 100 as p
    from veiculos.origem where segmento = 'leves' and origem = 'China'
)
select
    (select p from quatro order by ano desc limit 1)                        as quatro_agora,
    (select p from quatro order by ano desc limit 1) - (select p from quatro where ano = 2003) as quatro_desde_2003,
    (select p from china order by ano desc limit 1)                         as china_agora,
    (select p from china order by ano desc limit 1) - (select p from china where ano = 2020) as china_desde_2020
```

## Ranking

<DataTable data={ranking} rows=20 search=true>
    <Column id=posicao title="#" />
    <Column id=marca title="Marca" />
    <Column id=pais_origem title="Origem" />
    <Column id=emplacamentos title="Emplacamentos" fmt='#,##0' />
    <Column id=participacao title="Participação" fmt=pct1 />
    <Column id=variacao title="vs. ano anterior" fmt=pct0 contentType=delta />
</DataTable>

## Evolução

<Dropdown data={opcoes_marca} name=comparar value=marca title="Comparar" multiple=true defaultValue={['5 maiores']}>
    <DropdownOption value="5 maiores" valueLabel="5 maiores" />
</Dropdown>

<Grid cols=2>
    <LineChart
        data={comparativo}
        x=mes
        y=emplacamentos
        series=marca
        yFmt='#,##0'
        title={periodo[0]?.anual ? 'Emplacamentos (média mensal do ano)' : 'Emplacamentos por mês'}
    />
    <LineChart
        data={comparativo}
        x=mes
        y=participacao
        series=marca
        yFmt=pct0
        title="Participação"
    />
</Grid>

## Quem ganha e quem perde espaço

<BigValue data={destaques} value=quatro_agora title="Fiat, VW, GM e Ford hoje" fmt=pct0 comparison=quatro_desde_2003 comparisonFmt=pct0 comparisonTitle="pontos desde 2003" />
<BigValue data={destaques} value=china_agora title="Marcas chinesas hoje" fmt=pct1 comparison=china_desde_2020 comparisonFmt=pct1 comparisonTitle="pontos desde 2020" />

<BarChart
    data={origem_por_ano}
    x=ano
    xFmt='0'
    y=emplacamentos
    series=origem
    type=stacked100
    sort=false
    title="Participação por origem da marca, desde 2003"
    seriesColors={{
        'China': '#c0392b',
        'Japão e Coreia do Sul': '#e8a33d',
        'Europa': '#2c6fbb',
        'Estados Unidos': '#1b3a5c',
        'Outros países': '#7a9a6b',
        'Outras marcas': '#c9ccd1'
    }}
/>

<Alert status="info">

Com Varejo ou Venda direta, cada marca soma os seus modelos das listas do canal: é um piso, que cobre de 88% a 100% do canal. [Metodologia](/metodologia)

</Alert>
