-- Uma linha com os números de destaque do último mês publicado (cabeçalho do dashboard e
-- mensagem do commit automático).

with mensal as (
    select * from {{ ref('fct_emplacamentos_mensal') }} where segmento = 'leves'
),

ultimo as (
    select * from mensal order by mes_referencia desc limit 1
),

ano_corrente as (
    select * from {{ ref('mart_emplacamentos_anual') }}
    where segmento = 'leves' and ano = (select ano from ultimo)
),

marca_lider as (
    select m.marca, cast(round(100.0 * m.emplacamentos / u.emplacamentos, 2) as decimal(5, 2)) as participacao_pct
    from {{ ref('int_emplacamentos__marcas') }} as m
    join ultimo as u using (mes_referencia, segmento)
    where not m.eh_outras
    order by m.emplacamentos desc
    limit 1
),

modelo_lider as (
    select m.modelo_completo, m.emplacamentos
    from {{ ref('int_emplacamentos__modelos') }} as m
    join ultimo as u using (mes_referencia)
    order by m.emplacamentos desc, m.modelo_completo
    limit 1
),

recorde as (
    select ano, emplacamentos
    from {{ ref('mart_emplacamentos_anual') }}
    where segmento = 'leves' and not ano_parcial
    order by emplacamentos desc
    limit 1
)

select
    u.mes_referencia                                as ultimo_mes,
    u.emplacamentos                                 as emplacamentos_ultimo_mes,
    u.variacao_ano_anterior_pct                     as variacao_ultimo_mes_pct,
    u.venda_direta_pct                              as venda_direta_ultimo_mes_pct,
    a.emplacamentos                                 as emplacamentos_acumulado_ano,
    a.variacao_ano_anterior_pct                     as variacao_acumulado_ano_pct,
    a.venda_direta_pct                              as venda_direta_acumulado_ano_pct,
    ml.marca                                        as marca_lider_ultimo_mes,
    ml.participacao_pct                             as participacao_marca_lider_pct,
    mo.modelo_completo                              as modelo_lider_ultimo_mes,
    mo.emplacamentos                                as emplacamentos_modelo_lider,
    r.ano                                           as ano_recorde,
    r.emplacamentos                                 as emplacamentos_ano_recorde,
    (select min(mes_referencia) from mensal)        as primeiro_mes

from ultimo as u
cross join ano_corrente as a
cross join marca_lider as ml
cross join modelo_lider as mo
cross join recorde as r
