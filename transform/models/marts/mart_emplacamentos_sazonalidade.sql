-- Pergunta 1. Peso típico de cada mês do ano: emplacamentos do mês ÷ média mensal do
-- próprio ano (1,00 = mês médio). Mediana dos anos completos, que não deixa um ano
-- atípico (2020, pandemia) puxar o padrão.

with mensal as (
    select * from {{ ref('int_emplacamentos__mensal') }}
),

anos_completos as (
    select ano, segmento, avg(emplacamentos) as media_mensal
    from mensal
    group by ano, segmento
    having count(*) = 12
)

select
    m.segmento,
    m.mes_do_ano,
    cast(round(median(m.emplacamentos / a.media_mensal), 3) as decimal(5, 3)) as indice_sazonal,
    cast(round(min(m.emplacamentos / a.media_mensal), 3) as decimal(5, 3))    as indice_minimo,
    cast(round(max(m.emplacamentos / a.media_mensal), 3) as decimal(5, 3))    as indice_maximo,
    count(*)                                                                   as qtd_anos

from mensal as m
join anos_completos as a using (ano, segmento)
group by m.segmento, m.mes_do_ano
order by m.segmento, m.mes_do_ano
