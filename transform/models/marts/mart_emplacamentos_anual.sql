-- Pergunta 1 e 2. Um registro por ano e segmento. O ano corrente vem marcado como parcial;
-- para ele, a variação compara com os mesmos meses do ano anterior.

with mensal as (
    select * from {{ ref('int_emplacamentos__mensal') }}
),

anual as (
    select
        ano,
        segmento,
        count(*)                                        as qtd_meses,
        max(mes_do_ano)                                 as ultimo_mes_do_ano,
        cast(sum(emplacamentos) as bigint)                              as emplacamentos,
        -- Canal: soma dos meses com canal (sem out/2003 e mar/2005)
        cast(sum(emplacamentos_venda_direta) as bigint)                 as emplacamentos_venda_direta,
        cast(sum(emplacamentos_varejo) as bigint)                       as emplacamentos_varejo,
        cast(sum(emplacamentos) filter (where venda_direta_pct is not null) as bigint) as emplacamentos_com_canal
    from mensal
    group by ano, segmento
),

mesmos_meses_ano_anterior as (
    select a.ano, a.segmento, cast(sum(m.emplacamentos) as bigint) as emplacamentos
    from anual as a
    join mensal as m
      on m.ano = a.ano - 1 and m.segmento = a.segmento and m.mes_do_ano <= a.ultimo_mes_do_ano
    group by a.ano, a.segmento
)

select
    a.ano,
    a.segmento,
    a.qtd_meses < 12                                                    as ano_parcial,
    a.qtd_meses,
    a.emplacamentos,
    p.emplacamentos                                                     as emplacamentos_mesmos_meses_ano_anterior,
    cast(round(100.0 * (a.emplacamentos - p.emplacamentos) / p.emplacamentos, 1) as decimal(6, 1)) as variacao_ano_anterior_pct,
    a.emplacamentos_venda_direta,
    a.emplacamentos_varejo,
    cast(round(100.0 * a.emplacamentos_venda_direta / a.emplacamentos_com_canal, 1) as decimal(5, 1)) as venda_direta_pct,
    a.emplacamentos_com_canal < a.emplacamentos                         as canal_incompleto

from anual as a
left join mesmos_meses_ano_anterior as p using (ano, segmento)
order by a.ano, a.segmento
