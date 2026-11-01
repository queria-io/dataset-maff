# dataset-maff

農林水産省の筆ポリゴン（農地の区画情報）を Queria のカタログ（[data.queria.io](https://data.queria.io/)）へ取り込むデータセットです。

## データ出典

農林水産省「[地域の農業を見て・知って・活かすDB](https://www.maff.go.jp/j/tokei/census/shuraku_data/2025/mb/index.html)」の筆ポリゴンデータ（農業集落コード付き、FlatGeobuf）。筆ポリゴンそのものの説明は「[農地の区画情報（筆ポリゴン）のデータ提供・利用](https://www.maff.go.jp/j/tokei/porigon/)」にあります。

使うときは、筆ポリゴンの利用規約（政府標準利用規約 第2.0版に準拠）にしたがって、出典「筆ポリゴンデータ（2026年度公開）」（農林水産省）と、加工したものであることを書いてください。

## 収録テーブル

| テーブル | 内容 |
| --- | --- |
| `fude.field` | 1 行が 1 区画（田か畑の 1 枚）。耕地の種類、農業集落コード、市区町村コード、重心の経緯度、形 |

- 全国の 2026 年度公開データを収録しています
- 区画は航空写真・衛星画像を目視で判読して描いたもので、土地の権利関係や筆界を示すものではありません
- 農業集落コードは区画の重心が入る農業集落です。先頭 5 桁が市区町村コードです

```sql
-- 市区町村ごとの田と畑の面積（ha）
SELECT lg_code, land_type_name,
       count(*) AS fields,
       round(sum(ST_Area_Spheroid(ST_FlipCoordinates(geometry))) / 1e4) AS hectares
FROM maff.fude.field
WHERE city_code LIKE '13%'
GROUP BY ALL
ORDER BY hectares DESC;
```

## 変換のしかた

都道府県ごとの分割 zip を取ってつなぎ、中の FlatGeobuf を DuckDB の spatial 拡張で読んで Parquet にします。全国で zip が 5.4GB あるので、都道府県ごとに Parquet にしたそばから zip と FlatGeobuf を消します。Parquet が既にある都道府県は取り直しません。都道府県を絞るときは環境変数 `MAFF_PREFECTURES`（都道府県コードのカンマ区切り）を使います。

## ビルド

```bash
git submodule update --init
uv sync
scripts/build.sh                         # 全国
MAFF_PREFECTURES=13,14 scripts/build.sh  # 東京都と神奈川県だけ
```

Sync は手動実行だけです。
