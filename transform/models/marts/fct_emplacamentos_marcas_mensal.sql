-- Pergunta 3, mês a mês. Um registro por mês, segmento e marca do ranking da Fenabrave,
-- com a participação no segmento e a posição no mês. "Outras" fica fora (eh_outras no
-- intermediário); a participação é sobre o total do segmento, então as marcas listadas
-- somam um pouco menos de 100%.

with marcas as (
    select * from {{ ref('int_emplacamentos__marcas') }} where not eh_outras
),

totais as (
    select mes_referencia, segmento, emplacamentos as total
    from {{ ref('stg_fenabrave__segmentos') }}
)

select
    m.mes_referencia,
    year(m.mes_referencia)                                              as ano,
    m.segmento,
    row_number() over (partition by m.mes_referencia, m.segmento order by m.emplacamentos desc, m.marca) as posicao,
    m.marca,
    m.pais_origem,
    {{ grupo_origem('m.pais_origem') }}                                 as origem,
    cast(m.emplacamentos as bigint)                                     as emplacamentos,
    cast(round(100.0 * m.emplacamentos / t.total, 2) as decimal(5, 2))  as participacao_pct

from marcas as m
join totais as t using (mes_referencia, segmento)
order by m.mes_referencia, m.segmento, posicao
