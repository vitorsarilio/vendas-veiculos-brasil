-- Um registro por mês e modelo, com categoria, carroceria e marca padronizadas.
-- As listas por categoria trazem os mais emplacados (às vezes pulam posições), então a
-- soma de um modelo no ano é um piso. Out/2003 e mar/2005 não têm a tabela de modelos.

select
    m.mes_referencia,
    year(m.mes_referencia)                          as ano,
    m.segmento,
    c.categoria,
    c.carroceria,
    coalesce(s.marca, m.marca_fonte)                as marca,
    coalesce(s.pais_origem, 'Não classificado')     as pais_origem,
    m.modelo,
    coalesce(s.marca, m.marca_fonte) || ' ' || m.modelo as modelo_completo,
    m.emplacamentos

from {{ ref('stg_fenabrave__modelos') }} as m
join {{ ref('categorias') }} as c using (categoria_fonte)
left join {{ ref('marcas') }} as s using (marca_fonte)
