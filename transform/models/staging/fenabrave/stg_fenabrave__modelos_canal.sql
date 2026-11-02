-- Um registro por mês, canal, segmento e modelo. O modelo vem como "MARCA/MODELO", igual
-- às tabelas por categoria. Cada canal lista só os mais emplacados (~50 automóveis e ~40
-- comerciais leves), então a soma de uma marca ou de um modelo é um piso.
-- Out/2003 e mar/2005 (edições resumidas) e set/2023 (reconstruído) não têm a tabela.

with fonte as (
    select * from {{ source('fenabrave', 'fenabrave_modelos_canal') }}
)

select
    {{ mes_para_data('mes') }}                              as mes_referencia,
    canal,
    segmento,
    cast(posicao as integer)                                as posicao,
    {{ texto('modelo') }}                                   as modelo_fonte,
    -- Erros de digitação de nov/2013: "/ELANTRA" sem a marca (como na tabela por categoria)
    -- e "PONTIAC/MONTANA" no lugar de GM/MONTANA, que some da lista naquele mês
    case when trim(modelo) = '/ELANTRA' then 'HYUNDAI'
         when trim(modelo) = 'PONTIAC/MONTANA' then 'GM'
         else {{ texto("split_part(modelo, '/', 1)") }}
    end                                                     as marca_fonte,
    {{ texto("substr(modelo, strpos(modelo, '/') + 1)") }}  as modelo,
    {{ inteiro_br('quantidade') }}                          as emplacamentos,
    origem,
    arquivo                                                 as arquivo_fonte

from fonte
