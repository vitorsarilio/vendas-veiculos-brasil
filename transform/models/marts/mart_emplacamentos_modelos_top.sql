-- Pergunta 4. Os 10 modelos mais emplacados de cada ano (automóveis e comerciais leves
-- juntos), mais o top 10 de cada segmento. A soma anual é um piso: um modelo que saiu da
-- lista da categoria em algum mês não tem aquele mês contado.

with por_ano as (
    select
        ano,
        segmento,
        marca,
        modelo,
        modelo_completo,
        -- Um modelo pode mudar de categoria; fica a de maior volume no ano
        arg_max(categoria, emplacamentos)       as categoria,
        arg_max(carroceria, emplacamentos)      as carroceria,
        cast(sum(emplacamentos) as bigint)                      as emplacamentos,
        count(distinct mes_referencia)          as qtd_meses_listado
    from {{ ref('int_emplacamentos__modelos') }}
    group by ano, segmento, marca, modelo, modelo_completo
),

meses_do_ano as (
    select ano, count(distinct mes_referencia) as qtd_meses_com_modelos
    from {{ ref('int_emplacamentos__modelos') }}
    group by ano
),

ranqueado as (
    select
        *,
        row_number() over (partition by ano order by emplacamentos desc, modelo_completo)            as posicao_leves,
        row_number() over (partition by ano, segmento order by emplacamentos desc, modelo_completo)  as posicao_segmento
    from por_ano
)

select
    r.ano,
    a.qtd_meses_com_modelos < 12 as ano_incompleto,
    r.segmento,
    r.posicao_leves,
    r.posicao_segmento,
    r.marca,
    r.modelo,
    r.modelo_completo,
    r.categoria,
    r.carroceria,
    r.emplacamentos,
    r.qtd_meses_listado
from ranqueado as r
join meses_do_ano as a using (ano)
where r.posicao_leves <= 10 or r.posicao_segmento <= 10
order by r.ano, r.posicao_leves, r.segmento
