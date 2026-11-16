{# 筆ポリゴン。1 行が 1 区画（田か畑の 1 枚）。地域で引くので農業集落コードの順に並べる。 #}

select p.* exclude (source_prefecture_code), f.sha256 as source_sha256
from {{ ref('stg_field') }} p
join {{ ref('stg_fude_source_file') }} f on f.prefecture_code = p.source_prefecture_code and f.url is null
order by p.agricultural_community_code, p.lat, p.lng
