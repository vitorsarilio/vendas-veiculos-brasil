-- Um registro por mês, categoria e modelo. O modelo vem como "MARCA/MODELO" ("GM/ONIX").
-- Cada categoria lista os mais emplacados, então a soma de um ano é um piso para modelos
-- que saíram da lista em algum mês.

with fonte as (
    select * from {{ source('fenabrave', 'fenabrave_modelos') }}
)

select
    {{ mes_para_data('mes') }}                              as mes_referencia,
    segmento,
    {{ texto('categoria') }}                                as categoria_fonte,
    cast(posicao as integer)                                as posicao,
    {{ texto('modelo') }}                                   as modelo_fonte,
    -- Nov/2013 traz "/ELANTRA" sem a marca (erro de digitação do PDF)
    case when trim(modelo) = '/ELANTRA' then 'HYUNDAI'
         else {{ texto("split_part(modelo, '/', 1)") }}
    end                                                     as marca_fonte,
    {{ texto("substr(modelo, strpos(modelo, '/') + 1)") }}  as modelo,
    {{ inteiro_br('mes_atual') }}                           as emplacamentos,
    {{ inteiro_br('acumulado_ano') }}                       as emplacamentos_acumulado_ano,
    origem,
    arquivo                                                 as arquivo_fonte

from fonte
