-- Um registro por mês e segmento: % de varejo e % de venda direta (locadoras, frotistas,
-- PcD, táxi, governo). Até jun/2024 com 2 casas (lidas das imagens); depois, 1 casa.

with fonte as (
    select * from {{ source('fenabrave', 'fenabrave_canal') }}
)

select
    {{ mes_para_data('mes') }}                  as mes_referencia,
    segmento,
    {{ percentual('venda_direta_pct') }}        as venda_direta_pct,
    {{ percentual('varejo_pct') }}              as varejo_pct,
    case when origem like 'imagem%' then 2 else 1 end as casas_decimais,
    origem,
    arquivo                                     as arquivo_fonte

from fonte
