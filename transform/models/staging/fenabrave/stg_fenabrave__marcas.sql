-- Um registro por mês, segmento e marca do ranking. O nome vem como no PDF (`marca_fonte`);
-- a padronização (GM → Chevrolet, Chery → Caoa Chery…) é feita com o seed marcas.

with fonte as (
    select * from {{ source('fenabrave', 'fenabrave_marcas') }}
)

select
    {{ mes_para_data('mes') }}              as mes_referencia,
    segmento,
    cast(posicao as integer)                as posicao,
    {{ texto('marca') }}                    as marca_fonte,
    {{ inteiro_br('quantidade') }}          as emplacamentos,
    -- Nula em jan/2022 (automóveis calculados pela diferença) e em set/2023 vem recalculada
    {{ percentual('participacao') }}        as participacao_pct,
    origem,
    arquivo                                 as arquivo_fonte

from fonte
