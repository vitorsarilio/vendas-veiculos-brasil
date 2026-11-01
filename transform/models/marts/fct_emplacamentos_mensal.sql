-- Pergunta 1 e 2. Um registro por mês e segmento: emplacamentos, comparação com o mesmo
-- mês do ano anterior, média móvel de 12 meses e a divisão varejo × venda direta.

with mensal as (
    select * from {{ ref('int_emplacamentos__mensal') }}
)

select
    mes_referencia,
    ano,
    mes_do_ano,
    segmento,
    emplacamentos,
    lag(emplacamentos, 12) over w                                       as emplacamentos_mesmo_mes_ano_anterior,
    cast(round(100.0 * (emplacamentos - lag(emplacamentos, 12) over w)
               / lag(emplacamentos, 12) over w, 1) as decimal(6, 1))   as variacao_ano_anterior_pct,
    -- Só a partir do 12º mês da série (antes a janela estaria incompleta)
    case when row_number() over w >= 12
         then cast(round(avg(emplacamentos) over (w rows between 11 preceding and current row)) as integer)
    end                                                                 as media_movel_12m,
    venda_direta_pct,
    varejo_pct,
    emplacamentos_venda_direta,
    emplacamentos_varejo,
    casas_decimais_canal,
    origem_volume,
    origem_canal

from mensal
window w as (partition by segmento order by mes_referencia)
-- Ordem total: os Parquet saem idênticos a cada execução (o commit do CI depende disso)
order by segmento, mes_referencia
