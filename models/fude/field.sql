{# 筆ポリゴン。1 行が 1 区画（田か畑の 1 枚）。pipelines/fude.py が都道府県ごとに書いた Parquet を束ねる。
   地域で引くので農業集落コードの順に並べる。農業集落コードの先頭 5 桁は市区町村コード。 #}

select
    polygon_uuid,
    cast(land_type as integer) as land_type,
    case land_type when 100 then '田' when 200 then '畑' end as land_type_name,
    key as agricultural_community_code,
    substr(key, 1, 5) as city_code,
    {{ local_government_code('substr(key, 1, 5)') }} as lg_code,
    cast(issue_year as integer) as issue_year,
    point_lng as lng,
    point_lat as lat,
    st_geomfromwkb(geometry) as geometry
from read_parquet('data/maff/fude/*.parquet')
order by agricultural_community_code, lat, lng
