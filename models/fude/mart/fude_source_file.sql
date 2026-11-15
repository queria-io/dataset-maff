{{ config(alias='source_file') }}

{# 筆ポリゴンの元のファイル。1 行が分割 zip 1 つか、それをつないだ zip 1 つ。 #}

select url, page_url, sha256, bytes, media_type, retrieved_at, etag, last_modified, file, prefecture_code
from {{ ref('stg_fude_source_file') }}
order by file
