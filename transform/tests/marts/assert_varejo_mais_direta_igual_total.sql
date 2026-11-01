-- Nos meses com canal, varejo + venda direta = total do segmento (em unidades).
select mes_referencia, segmento
from {{ ref('fct_emplacamentos_mensal') }}
where venda_direta_pct is not null
  and emplacamentos_varejo + emplacamentos_venda_direta <> emplacamentos
