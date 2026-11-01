{#
  Teste genérico: a proporção de nulos na coluna não pode passar de `maximo` (0 a 1).
  Útil quando alguns nulos são esperados (ex.: datas de preenchimento da fonte),
  mas um aumento repentino indica que algo mudou na origem.
#}
{% test proporcao_nulos_maxima(model, column_name, maximo) %}

with contagem as (
    select
        count(*) as total,
        count(*) filter (where {{ column_name }} is null) as nulos
    from {{ model }}
)

select *
from contagem
where total = 0
   or nulos * 1.0 / total > {{ maximo }}

{% endtest %}


{#
  Teste genérico de modelo: o número de linhas precisa ficar entre `minimo` e `maximo`.
  Pega mudanças silenciosas na fonte (API devolvendo menos registros, filtro errado).
#}
{% test quantidade_linhas_entre(model, minimo, maximo) %}

select count(*) as linhas
from {{ model }}
having count(*) not between {{ minimo }} and {{ maximo }}

{% endtest %}
