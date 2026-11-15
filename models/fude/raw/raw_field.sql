{# 筆ポリゴンの FlatGeobuf を、pipelines/fude.py が都道府県ごとに Parquet にしたもの。列はそのまま（形は WKB）。 #}

select * from read_parquet('data/maff/fude/*.parquet')
