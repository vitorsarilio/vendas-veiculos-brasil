---
title: Canais
sidebar_position: 2
---

```sql meses_crescente
select strftime(mes_referencia, '%Y-%m') as mes, strftime(mes_referencia, '%m/%Y') as mes_nome
from veiculos.mensal where segmento = 'leves' order by mes
```

```sql meses_decrescente
select strftime(mes_referencia, '%Y-%m') as mes, strftime(mes_referencia, '%m/%Y') as mes_nome
from veiculos.mensal where segmento = 'leves' order by mes desc
```

<Dropdown data={meses_crescente} name=inicio value=mes label=mes_nome order=mes title="De" />
<Dropdown data={meses_decrescente} name=fim value=mes label=mes_nome order="mes desc" title="Até" />
<ButtonGroup name=segmento>
    <ButtonGroupItem valueLabel="Leves" value="leves" default />
    <ButtonGroupItem valueLabel="Automóveis" value="automoveis" />
    <ButtonGroupItem valueLabel="Comerciais leves" value="comerciais_leves" />
</ButtonGroup>

```sql no_periodo
-- Cada ano soma só os meses entre "De" e "Até"; meses sem o dado de canal ficam de fora
select
    cast(ano as integer)                                as ano,
    segmento,
    sum(emplacamentos_venda_direta) / sum(emplacamentos) filter (where venda_direta_pct is not null) as venda_direta,
    sum(emplacamentos_venda_direta)                     as emplacamentos_venda_direta,
    sum(emplacamentos_varejo)                           as emplacamentos_varejo
from veiculos.mensal
where strftime(mes_referencia, '%Y-%m') between '${inputs.inicio.value}' and '${inputs.fim.value}'
group by all
```

```sql anual
select
    cast(ano as integer)                as ano,
    segmento,
    venda_direta_pct / 100              as venda_direta,
    emplacamentos_venda_direta,
    emplacamentos_varejo,
    ano_parcial
from veiculos.anual
order by ano
```

```sql unidades_por_canal
select ano, 'Venda direta' as canal, emplacamentos_venda_direta as emplacamentos from ${no_periodo} where segmento = '${inputs.segmento}'
union all
select ano, 'Varejo', emplacamentos_varejo from ${no_periodo} where segmento = '${inputs.segmento}'
order by ano, canal desc
```

```sql participacao_por_segmento
select
    make_date(ano, 7, 1) + interval 12 hour as ano,
    case segmento when 'automoveis' then 'Automóveis' when 'comerciais_leves' then 'Comerciais leves' else 'Total de leves' end as segmento,
    venda_direta
from ${no_periodo}
order by ano, segmento
```

```sql destaques
select
    (select venda_direta from ${anual} where segmento = 'leves' and ano = 2012) as em_2012,
    (select venda_direta from ${anual} where segmento = 'leves' and not ano_parcial order by ano desc limit 1) as ultimo_ano_completo,
    (select venda_direta from ${anual} where segmento = 'leves' and not ano_parcial order by ano desc limit 1)
        - (select venda_direta from ${anual} where segmento = 'leves' and ano = 2012) as desde_2012
```

## Varejo × venda direta

Venda direta é o que a montadora fatura direto para locadoras, frotistas, PcD, produtores rurais e governo; o resto é varejo.

<BigValue data={destaques} value=ultimo_ano_completo title="Venda direta no último ano completo" fmt=pct0 comparison=desde_2012 comparisonFmt=pct0 comparisonTitle="pontos desde 2012" />

<LineChart
    data={participacao_por_segmento}
    x=ano
    xFmt='yyyy'
    y=venda_direta
    series=segmento
    yFmt=pct0
    title="Venda direta, % dos emplacamentos"
/>

<BarChart
    data={unidades_por_canal}
    x=ano
    xFmt='0'
    y=emplacamentos
    series=canal
    sort=false
    yFmt='#,##0'
    title="Emplacamentos por canal"
    colorPalette={['#d1495b', '#1d4e89']}
/>

<Alert status="info">

Atacado (montadora → concessionária) é dado da Anfavea, não da Fenabrave. As unidades por canal são estimadas a partir do percentual publicado. [Metodologia](/metodologia)

</Alert>
