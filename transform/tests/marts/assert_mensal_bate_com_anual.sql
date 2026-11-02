-- Os marts mensais de marcas e modelos somam, por ano, o mesmo que os anuais.
with marcas as (
    select 'marcas' as mart, m.ano, m.segmento, sum(m.emplacamentos) as mensal, any_value(a.anual) as anual
    from {{ ref('fct_emplacamentos_marcas_mensal') }} as m
    join (
        select ano, segmento, sum(emplacamentos) as anual
        from {{ ref('mart_emplacamentos_marcas') }} where not eh_outras group by all
    ) as a using (ano, segmento)
    group by m.ano, m.segmento
),

modelos as (
    select 'modelos' as mart, m.ano, m.segmento, sum(m.emplacamentos) as mensal, any_value(a.anual) as anual
    from {{ ref('fct_emplacamentos_modelos_mensal') }} as m
    join (
        select ano, segmento, sum(emplacamentos) as anual
        from {{ ref('mart_emplacamentos_modelos') }} group by all
    ) as a using (ano, segmento)
    group by m.ano, m.segmento
)

select * from marcas where mensal <> anual
union all
select * from modelos where mensal <> anual
