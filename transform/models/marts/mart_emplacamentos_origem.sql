-- Pergunta 3. Participação por origem da marca (país da marca, não da fábrica), por ano.
-- Mostra a subida das marcas chinesas. "Outras" (marcas fora do top ~20 do mês) fica em
-- "Não classificado".

with marcas as (
    select * from {{ ref('mart_emplacamentos_marcas') }}
)

select
    ano,
    ano_parcial,
    segmento,
    case
        when pais_origem = 'China' then 'China'
        when pais_origem in ('Japão', 'Coreia do Sul') then 'Japão e Coreia do Sul'
        when pais_origem in ('Alemanha', 'Itália', 'França', 'Reino Unido', 'Suécia', 'Espanha', 'Romênia') then 'Europa'
        when pais_origem = 'Estados Unidos' then 'Estados Unidos'
        when pais_origem = 'Não classificado' then 'Não classificado'
        else 'Outros países'
    end                                     as origem,
    cast(sum(emplacamentos) as bigint)                      as emplacamentos,
    cast(round(100.0 * sum(emplacamentos) / sum(sum(emplacamentos)) over (partition by ano, segmento), 2)
         as decimal(5, 2))                  as participacao_pct

from marcas
group by ano, ano_parcial, segmento, origem
order by ano, segmento, emplacamentos desc, origem
