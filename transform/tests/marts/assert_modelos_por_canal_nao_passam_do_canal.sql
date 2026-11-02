-- Os modelos listados em cada canal não passam das unidades do canal no mês (total do
-- segmento × % do canal), com folga de 1% do segmento pelo arredondamento do %.
with modelos as (
    select mes_referencia, segmento, canal, sum(emplacamentos) as modelos
    from {{ ref('fct_emplacamentos_modelos_canal_mensal') }}
    group by all
),

canal as (
    select mes_referencia, segmento, 'varejo' as canal, emplacamentos_varejo as unidades, emplacamentos
    from {{ ref('fct_emplacamentos_mensal') }}
    union all
    select mes_referencia, segmento, 'venda_direta', emplacamentos_venda_direta, emplacamentos
    from {{ ref('fct_emplacamentos_mensal') }}
)

select m.*, c.unidades
from modelos as m
join canal as c using (mes_referencia, segmento, canal)
where m.modelos > c.unidades + c.emplacamentos * 0.01
