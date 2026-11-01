-- Um registro por mês, segmento e marca padronizada. Nomes diferentes da mesma marca no
-- mesmo mês (raro) são somados. O ranking é um top ~20 por segmento: o que fica de fora
-- vira a linha "Outras" (total do segmento − soma das marcas listadas).

with marcas as (
    select
        m.mes_referencia,
        m.segmento,
        coalesce(s.marca, m.marca_fonte)                as marca,
        coalesce(s.pais_origem, 'Não classificado')     as pais_origem,
        sum(m.emplacamentos)                            as emplacamentos
    from {{ ref('stg_fenabrave__marcas') }} as m
    left join {{ ref('marcas') }} as s using (marca_fonte)
    group by all
),

outras as (
    select
        t.mes_referencia,
        t.segmento,
        'Outras'                                        as marca,
        'Não classificado'                              as pais_origem,
        t.emplacamentos - coalesce(sum(m.emplacamentos), 0) as emplacamentos
    from {{ ref('stg_fenabrave__segmentos') }} as t
    left join marcas as m using (mes_referencia, segmento)
    group by t.mes_referencia, t.segmento, t.emplacamentos
)

select *, false as eh_outras from marcas
union all
select *, true as eh_outras from outras
