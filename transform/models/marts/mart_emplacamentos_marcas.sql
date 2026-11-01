-- Pergunta 3. Um registro por ano, segmento e marca: emplacamentos, participação e posição.
-- Soma dos rankings mensais (top ~20); o que ficou de fora de cada mês entra em "Outras",
-- então a soma de um ano fecha com o total do segmento.

with marcas as (
    select
        year(mes_referencia)        as ano,
        segmento,
        marca,
        pais_origem,
        eh_outras,
        cast(sum(emplacamentos) as bigint)          as emplacamentos
    from {{ ref('int_emplacamentos__marcas') }}
    group by all
),

totais as (
    select ano, segmento, count(*) as qtd_meses, cast(sum(emplacamentos) as bigint) as total
    from {{ ref('int_emplacamentos__mensal') }}
    group by ano, segmento
)

select
    m.ano,
    t.qtd_meses < 12                                                         as ano_parcial,
    m.segmento,
    m.marca,
    m.pais_origem,
    m.eh_outras,
    m.emplacamentos,
    cast(round(100.0 * m.emplacamentos / t.total, 2) as decimal(5, 2))        as participacao_pct,
    case when not m.eh_outras
         then row_number() over (partition by m.ano, m.segmento, m.eh_outras order by m.emplacamentos desc, m.marca)
    end                                                                       as posicao

from marcas as m
join totais as t using (ano, segmento)
order by m.ano, m.segmento, m.emplacamentos desc, m.marca
