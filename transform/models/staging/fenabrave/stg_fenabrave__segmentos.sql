-- Um registro por mês e segmento. A série usa sempre a coluna do próprio mês (`mes_atual`);
-- as outras colunas do resumo ficam para conferência.

with fonte as (
    select * from {{ source('fenabrave', 'fenabrave_segmentos') }}
)

select
    {{ mes_para_data('mes') }}                          as mes_referencia,
    segmento,
    {{ inteiro_br('mes_atual') }}                       as emplacamentos,
    {{ inteiro_br('mes_anterior') }}                    as emplacamentos_mes_anterior,
    {{ inteiro_br('acumulado_ano') }}                   as emplacamentos_acumulado_ano,
    -- Nulos só no mês reconstruído (set/2023), que não tem essas colunas nos vizinhos
    {{ inteiro_br('mesmo_mes_ano_anterior') }}          as emplacamentos_mesmo_mes_ano_anterior,
    {{ inteiro_br('acumulado_ano_anterior') }}          as emplacamentos_acumulado_ano_anterior,
    origem,
    arquivo                                             as arquivo_fonte

from fonte
