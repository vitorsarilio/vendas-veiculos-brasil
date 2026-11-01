-- Um registro por mês e segmento: emplacamentos e a divisão entre varejo e venda direta.
-- As unidades por canal são % × total do segmento (a Fenabrave publica só o %): erro de
-- algumas unidades até jun/2024 (2 casas) e de até ~0,05% do total depois (1 casa).
-- Out/2003 e mar/2005 (edição resumida) ficam sem canal.

with segmentos as (
    select * from {{ ref('stg_fenabrave__segmentos') }}
),

canal as (
    select * from {{ ref('stg_fenabrave__canal') }}
)

select
    s.mes_referencia,
    year(s.mes_referencia)                                              as ano,
    month(s.mes_referencia)                                             as mes_do_ano,
    s.segmento,
    s.emplacamentos,
    c.venda_direta_pct,
    c.varejo_pct,
    cast(round(s.emplacamentos * c.venda_direta_pct / 100) as integer) as emplacamentos_venda_direta,
    s.emplacamentos
        - cast(round(s.emplacamentos * c.venda_direta_pct / 100) as integer) as emplacamentos_varejo,
    c.casas_decimais                                                    as casas_decimais_canal,
    s.origem                                                            as origem_volume,
    c.origem                                                            as origem_canal

from segmentos as s
left join canal as c using (mes_referencia, segmento)
