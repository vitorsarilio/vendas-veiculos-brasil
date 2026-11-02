---
title: Canais
sidebar_position: 2
---

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

```sql leves_anual_unidades
select ano, 'Venda direta' as canal, emplacamentos_venda_direta as emplacamentos from ${anual} where segmento = 'leves'
union all
select ano, 'Varejo', emplacamentos_varejo from ${anual} where segmento = 'leves'
order by ano, canal desc
```

```sql participacao_por_segmento
select
    ano,
    case segmento when 'automoveis' then 'Automóveis' when 'comerciais_leves' then 'Comerciais leves' else 'Total de leves' end as segmento,
    venda_direta
from ${anual}
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
where segmento = 'leves' and venda_direta_pct is not null
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
    data={leves_anual_unidades}
    x=ano
    xFmt='0'
    y=emplacamentos
    series=canal
    sort=false
    yFmt='#,##0'
    title="Veículos leves por canal (unidades estimadas)"
    colorPalette={['#d1495b', '#1d4e89']}
/>

<LineChart
    data={mensal}
    x=mes
    y=venda_direta
    yFmt=pct0
    title="Venda direta mês a mês (total de leves)"
/>

<Alert status="info">

**E o atacado?** Venda no atacado é o que a montadora fatura para as concessionárias, medido pela Anfavea, não pela Fenabrave. A Anfavea não publica essa série para carros num formato que dê para baixar automaticamente, então este painel mostra só o que chega ao cliente final (emplacamento), dividido entre varejo e venda direta.

As unidades por canal são estimadas: a Fenabrave publica o percentual de cada canal, e o painel multiplica pelo total do mês. Até jun/2024 o percentual tem 2 casas decimais (erro de poucas unidades); depois, 1 casa (erro de até ~0,05% do mês). Out/2003 e mar/2005 não têm o dado. [Detalhes na metodologia](/metodologia).

</Alert>
