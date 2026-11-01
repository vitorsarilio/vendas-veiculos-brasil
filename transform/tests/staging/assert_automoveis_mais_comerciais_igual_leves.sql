-- O total de leves do resumo tem que ser exatamente automóveis + comerciais leves.
select mes_referencia
from {{ ref('stg_fenabrave__segmentos') }}
group by mes_referencia
having sum(case when segmento = 'leves' then emplacamentos else -emplacamentos end) <> 0
