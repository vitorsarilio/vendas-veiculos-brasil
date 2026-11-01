-- Pergunta 4. Emplacamentos por tipo de carroceria e ano (soma das listas de modelos por
-- categoria). A participação é sobre o total listado do segmento; as listas cobrem quase
-- todo o mercado, então ela mostra bem a troca de hatches e sedãs por SUVs.

with por_ano as (
    select ano, segmento, carroceria, cast(sum(emplacamentos) as bigint) as emplacamentos
    from {{ ref('int_emplacamentos__modelos') }}
    group by all
),

meses_do_ano as (
    select ano, count(distinct mes_referencia) as qtd_meses_com_modelos
    from {{ ref('int_emplacamentos__modelos') }}
    group by ano
)

select
    p.ano,
    a.qtd_meses_com_modelos < 12                                             as ano_incompleto,
    p.segmento,
    p.carroceria,
    p.emplacamentos,
    cast(round(100.0 * p.emplacamentos / sum(p.emplacamentos) over (partition by p.ano, p.segmento), 2) as decimal(5, 2)) as participacao_no_segmento_pct,
    cast(round(100.0 * p.emplacamentos / sum(p.emplacamentos) over (partition by p.ano), 2) as decimal(5, 2))              as participacao_nos_leves_pct
from por_ano as p
join meses_do_ano as a using (ano)
order by p.ano, p.segmento, p.emplacamentos desc, p.carroceria
