-- Pergunta 3. Participação por origem da marca (país da marca, não da fábrica), por ano.
-- Mostra a subida das marcas chinesas. "Outras" (marcas fora do top ~20 do mês) fica em
-- "Não classificado". O agrupamento dos países está na macro grupo_origem.

select
    ano,
    ano_parcial,
    segmento,
    origem,
    cast(sum(emplacamentos) as bigint)      as emplacamentos,
    cast(round(100.0 * sum(emplacamentos) / sum(sum(emplacamentos)) over (partition by ano, segmento), 2)
         as decimal(5, 2))                  as participacao_pct

from {{ ref('mart_emplacamentos_marcas') }}
group by ano, ano_parcial, segmento, origem
order by ano, segmento, emplacamentos desc, origem
