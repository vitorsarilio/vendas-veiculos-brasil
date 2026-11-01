-- O ranking é um top ~20: a soma das marcas pode ficar abaixo do total do segmento, nunca acima.
select m.mes_referencia, m.segmento, sum(m.emplacamentos) as soma_marcas, s.emplacamentos as total
from {{ ref('stg_fenabrave__marcas') }} as m
join {{ ref('stg_fenabrave__segmentos') }} as s using (mes_referencia, segmento)
group by m.mes_referencia, m.segmento, s.emplacamentos
having sum(m.emplacamentos) > s.emplacamentos
