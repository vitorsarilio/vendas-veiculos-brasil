-- Reconciliação: os totais de cada mart por ano e segmento batem com a soma mensal
-- (nenhum emplacamento some nem é contado duas vezes). Retorna as linhas que não batem.

with base as (
    select ano, segmento, sum(emplacamentos) as total
    from {{ ref('fct_emplacamentos_mensal') }}
    group by ano, segmento
),

marts as (
    select 'mart_emplacamentos_anual' as mart, ano, segmento, emplacamentos as total
    from {{ ref('mart_emplacamentos_anual') }}
    union all
    select 'mart_emplacamentos_marcas', ano, segmento, sum(emplacamentos)
    from {{ ref('mart_emplacamentos_marcas') }}
    group by ano, segmento
    union all
    select 'mart_emplacamentos_origem', ano, segmento, sum(emplacamentos)
    from {{ ref('mart_emplacamentos_origem') }}
    group by ano, segmento
)

select m.mart, m.ano, m.segmento, m.total as total_mart, b.total as total_esperado
from marts as m
join base as b using (ano, segmento)
where m.total <> b.total
