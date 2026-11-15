{# 筆ポリゴン。1 行が 1 区画（田か畑の 1 枚）。地域で引くので農業集落コードの順に並べる。 #}

select *
from {{ ref('stg_field') }}
order by agricultural_community_code, lat, lng
