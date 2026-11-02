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

<Dropdown data={meses_crescente} name=inicio value=mes label=mes_nome order=mes title="De (mês/ano)" />
<Dropdown data={meses_decrescente} name=fim value=mes label=mes_nome order="mes desc" title="Até (mês/ano)" />
<ButtonGroup name=segmento title="Segmento (gráficos de unidades e mês a mês)">
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
    ano,
    case segmento when 'automoveis' then 'Automóveis' when 'comerciais_leves' then 'Comerciais leves' else 'Total de leves' end as segmento,
    venda_direta
from ${no_periodo}
order by ano, segmento
```

```sql destaques
select
    (select venda_direta from ${anual} where segmento = 'leves' and ano = 2012) as em_2012,
    (select venda_direta from ${anual} where segmento = 'leves' and not ano_parcial order by ano desc limit 1) as ultimo_ano_completo,
    (select ano from ${anual} where segmento = 'leves' and not ano_parcial order by ano desc limit 1) as ultimo_ano
```

```sql mensal
select
    mes_referencia + interval 12 hour   as mes,
    venda_direta_pct / 100              as venda_direta
from veiculos.mensal
where segmento = '${inputs.segmento}' and venda_direta_pct is not null
  and strftime(mes_referencia, '%Y-%m') between '${inputs.inicio.value}' and '${inputs.fim.value}'
order by mes_referencia
```

## Varejo × venda direta

A Fenabrave separa os emplacamentos em dois canais:

- **Varejo**: o consumidor compra na concessionária.
- **Venda direta**: a montadora fatura direto para o cliente, com condições especiais. São locadoras, frotistas, produtores rurais, taxistas, pessoas com deficiência (PcD) e governo.

A venda direta foi de <Value data={destaques} column=em_2012 fmt=pct0 /> dos leves em 2012 para **<Value data={destaques} column=ultimo_ano_completo fmt=pct0 />** em <Value data={destaques} column=ultimo_ano fmt='0' />. O motor foi o boom das locadoras e da assinatura de carros, que passaram a comprar boa parte da produção.

<LineChart
    data={participacao_por_segmento}
    x=ano
    xFmt='0'
    y=venda_direta
    series=segmento
    yFmt=pct0
    title="Participação da venda direta por ano"
    subtitle="Comerciais leves sempre tiveram mais venda direta (frotas de empresas e do agro)"
/>

<BarChart
    data={unidades_por_canal}
    x=ano
    xFmt='0'
    y=emplacamentos
    series=canal
    sort=false
    yFmt='#,##0'
    title="Emplacamentos por canal (unidades estimadas)"
    colorPalette={['#d1495b', '#1d4e89']}
/>

<LineChart
    data={mensal}
    x=mes
    y=venda_direta
    yFmt=pct0
    title="Venda direta mês a mês"
/>

<Alert status="info">

**E o atacado?** Venda no atacado é o que a montadora fatura para as concessionárias, medido pela Anfavea, não pela Fenabrave. A Anfavea não publica essa série para carros num formato que dê para baixar automaticamente, então este painel mostra só o que chega ao cliente final (emplacamento), dividido entre varejo e venda direta.

As unidades por canal são estimadas: a Fenabrave publica o percentual de cada canal, e o painel multiplica pelo total do mês. Até jun/2024 o percentual tem 2 casas decimais (erro de poucas unidades); depois, 1 casa (erro de até ~0,05% do mês). Out/2003 e mar/2005 não têm o dado. [Detalhes na metodologia](/metodologia).

</Alert>
