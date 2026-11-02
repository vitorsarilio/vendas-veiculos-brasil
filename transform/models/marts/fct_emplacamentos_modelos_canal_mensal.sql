-- Varejo × venda direta por modelo, mês a mês. Um registro por mês, canal e modelo listado.
-- As tabelas por canal não trazem a categoria: ela vem das tabelas por categoria (a mais
-- frequente do modelo na série). Modelos que nunca aparecem nelas ficam "Não classificado".

with categoria_do_modelo as (
    select
        segmento,
        modelo_completo,
        arg_max(categoria, emplacamentos)   as categoria,
        arg_max(carroceria, emplacamentos)  as carroceria
    from (
        select segmento, modelo_completo, categoria, carroceria, sum(emplacamentos) as emplacamentos
        from {{ ref('int_emplacamentos__modelos') }}
        group by all
    )
    group by all
),

modelos as (
    select
        m.mes_referencia,
        year(m.mes_referencia)                          as ano,
        m.canal,
        m.segmento,
        coalesce(s.marca, m.marca_fonte)                as marca,
        coalesce(s.pais_origem, 'Não classificado')     as pais_origem,
        m.modelo,
        coalesce(s.marca, m.marca_fonte) || ' ' || m.modelo as modelo_completo,
        m.emplacamentos
    from {{ ref('stg_fenabrave__modelos_canal') }} as m
    left join {{ ref('marcas') }} as s using (marca_fonte)
)

select
    m.mes_referencia,
    m.ano,
    m.canal,
    m.segmento,
    m.marca,
    m.pais_origem,
    {{ grupo_origem('m.pais_origem') }}             as origem,
    m.modelo,
    m.modelo_completo,
    coalesce(c.categoria, 'Não classificado')       as categoria,
    coalesce(c.carroceria, 'Não classificado')      as carroceria,
    cast(sum(m.emplacamentos) as bigint)            as emplacamentos

from modelos as m
left join categoria_do_modelo as c using (segmento, modelo_completo)
group by all
order by m.mes_referencia, m.canal, m.segmento, 12 desc, m.modelo_completo
