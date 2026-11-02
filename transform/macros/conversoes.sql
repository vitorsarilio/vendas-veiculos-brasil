{#
  Conversões usadas no staging. O dado bruto chega todo como texto, fiel ao PDF.
#}

{# Contagem no formato do relatório ("1.234"). Zero aparece como "0,00", "0,0" ou "-". #}
{% macro inteiro_br(coluna) -%}
    case
        when trim({{ coluna }}) in ('-', '0,00', '0,0') then 0
        else cast(replace(trim({{ coluna }}), '.', '') as integer)
    end
{%- endmacro %}


{# Percentual "21,51%" (vírgula) ou "46.3" (ponto, sem %) para decimal(6,2) em pontos percentuais. #}
{% macro percentual(coluna) -%}
    cast(replace(replace(trim({{ coluna }}), '%', ''), ',', '.') as decimal(6, 2))
{%- endmacro %}


{# 'AAAA-MM' para o primeiro dia do mês. #}
{% macro mes_para_data(coluna) -%}
    cast({{ coluna }} || '-01' as date)
{%- endmacro %}


{# Texto limpo: tira espaços das pontas, o hífen invisível (U+00AD) e transforma vazio em nulo. #}
{% macro texto(coluna) -%}
    nullif(trim(replace({{ coluna }}, chr(173), '-')), '')
{%- endmacro %}


{# Agrupamento do país de origem da marca usado no painel (China, Europa, Japão e Coreia…). #}
{% macro grupo_origem(coluna) -%}
    case
        when {{ coluna }} = 'China' then 'China'
        when {{ coluna }} in ('Japão', 'Coreia do Sul') then 'Japão e Coreia do Sul'
        when {{ coluna }} in ('Alemanha', 'Itália', 'França', 'Reino Unido', 'Suécia', 'Espanha', 'Romênia') then 'Europa'
        when {{ coluna }} = 'Estados Unidos' then 'Estados Unidos'
        when {{ coluna }} = 'Não classificado' then 'Não classificado'
        else 'Outros países'
    end
{%- endmacro %}
