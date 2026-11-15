{# 筆ポリゴンの FlatGeobuf を、pipelines/fude.py が都道府県ごとに Parquet にしたもの。列はそのまま（形は WKB）。
   filename は読んだ Parquet の置き場所で、名前が都道府県コード。 #}

select * from read_parquet('data/maff/fude/*.parquet', filename = true)
