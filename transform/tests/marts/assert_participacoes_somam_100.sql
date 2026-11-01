-- Participações de marca, origem e carroceria somam 100% por ano e segmento
-- (tolerância de arredondamento: 0,1 p.p. por linha de mart).
select 'marcas' as mart, ano, segmento, sum(participacao_pct) as soma
from {{ ref('mart_emplacamentos_marcas') }}
group by ano, segmento
having abs(sum(participacao_pct) - 100) > 0.5
union all
select 'origem', ano, segmento, sum(participacao_pct)
from {{ ref('mart_emplacamentos_origem') }}
group by ano, segmento
having abs(sum(participacao_pct) - 100) > 0.1
union all
select 'carroceria', ano, segmento, sum(participacao_no_segmento_pct)
from {{ ref('mart_emplacamentos_carroceria') }}
group by ano, segmento
having abs(sum(participacao_no_segmento_pct) - 100) > 0.1
