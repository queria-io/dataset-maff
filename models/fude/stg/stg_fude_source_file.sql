{# 取得の記録に型を付ける。 #}

select
    prefecture_code,
    file,
    url,
    page_url,
    sha256,
    bytes,
    media_type,
    cast(retrieved_at as timestamptz) as retrieved_at,
    etag,
    last_modified
from {{ ref('raw_fude_source_file') }}
