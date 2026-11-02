-- Pergunta 4, mês a mês. Um registro por mês e modelo listado pela Fenabrave, com
-- categoria, carroceria, marca e origem. Out/2003 e mar/2005 não têm a tabela de modelos.

select
    mes_referencia,
    ano,
    segmento,
    row_number() over (partition by mes_referencia order by sum(emplacamentos) desc, modelo_completo) as posicao_leves,
    marca,
    pais_origem,
    {{ grupo_origem('pais_origem') }}               as origem,
    modelo,
    modelo_completo,
    arg_max(categoria, emplacamentos)               as categoria,
    arg_max(carroceria, emplacamentos)              as carroceria,
    cast(sum(emplacamentos) as bigint)              as emplacamentos

from {{ ref('int_emplacamentos__modelos') }}
group by mes_referencia, ano, segmento, marca, pais_origem, modelo, modelo_completo
order by mes_referencia, posicao_leves
