{# 筆ポリゴンの分割 zip とつないだ zip の取得の記録。pipelines/fude.py が data/maff/fude/source_file.ndjson に書いたものをそのまま読む。 #}

select *
from read_json(
    'data/maff/fude/source_file.ndjson',
    format = 'newline_delimited',
    columns = {
        prefecture_code: 'VARCHAR',
        file: 'VARCHAR',
        url: 'VARCHAR',
        page_url: 'VARCHAR',
        sha256: 'VARCHAR',
        bytes: 'BIGINT',
        media_type: 'VARCHAR',
        retrieved_at: 'VARCHAR',
        etag: 'VARCHAR',
        last_modified: 'VARCHAR'
    }
)
