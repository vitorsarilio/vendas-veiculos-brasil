-- Um mês por linha, de jan/2003 até o último publicado, sem buracos.
with meses as (
    select distinct mes_referencia from {{ ref('stg_fenabrave__segmentos') }}
),

esperados as (
    select unnest(generate_series(date '2003-01-01', (select max(mes_referencia) from meses), interval 1 month))::date as mes_referencia
)

select e.mes_referencia
from esperados as e
left join meses as m using (mes_referencia)
where m.mes_referencia is null
