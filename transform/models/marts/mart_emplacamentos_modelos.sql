-- Pergunta 4. Todos os modelos listados pela Fenabrave, por ano: emplacamentos, categoria,
-- carroceria, marca e origem, com a posição no ano (no total de leves e no segmento).
-- A soma anual é um piso: um modelo que saiu da lista da categoria em algum mês não tem
-- aquele mês contado.

with por_ano as (
    select
        ano,
        segmento,
        marca,
        pais_origem,
        modelo,
        modelo_completo,
        -- Um modelo pode mudar de categoria; fica a de maior volume no ano
        arg_max(categoria, emplacamentos)       as categoria,
        arg_max(carroceria, emplacamentos)      as carroceria,
        cast(sum(emplacamentos) as bigint)      as emplacamentos,
        count(distinct mes_referencia)          as qtd_meses_listado
    from {{ ref('int_emplacamentos__modelos') }}
    group by ano, segmento, marca, pais_origem, modelo, modelo_completo
),

meses_do_ano as (
    select ano, count(distinct mes_referencia) as qtd_meses_com_modelos
    from {{ ref('int_emplacamentos__modelos') }}
    group by ano
)

select
    p.ano,
    a.qtd_meses_com_modelos < 12 as ano_incompleto,
    p.segmento,
    row_number() over (partition by p.ano order by p.emplacamentos desc, p.modelo_completo)              as posicao_leves,
    row_number() over (partition by p.ano, p.segmento order by p.emplacamentos desc, p.modelo_completo)  as posicao_segmento,
    p.marca,
    p.pais_origem,
    {{ grupo_origem('p.pais_origem') }}     as origem,
    p.modelo,
    p.modelo_completo,
    p.categoria,
    p.carroceria,
    p.emplacamentos,
    p.qtd_meses_listado
from por_ano as p
join meses_do_ano as a using (ano)
order by p.ano, posicao_leves, p.segmento
