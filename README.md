# 農林水産省 筆ポリゴン

農林水産省の筆ポリゴン（農地の区画情報）を、SQL で集計・地図表示できるテーブルにしたデータセットです。全国の田と畑を 1 枚ずつ区画の形で収録しています。農地の場所と広さを地図で見る、市区町村や農業集落ごとに田畑の数や面積を数える、農林業センサスの農業集落別の数字と結合する、といった使い方ができます。

## 出典と利用条件

農林水産省「[地域の農業を見て・知って・活かすDB](https://www.maff.go.jp/j/tokei/census/shuraku_data/2025/mb/index.html)」の筆ポリゴンデータ（農業集落コード付き、FlatGeobuf）を加工しています。筆ポリゴンそのものの説明は「[農地の区画情報（筆ポリゴン）のデータ提供・利用](https://www.maff.go.jp/j/tokei/porigon/)」にあります。

- 筆ポリゴンの利用規約（政府標準利用規約 第2.0版に準拠）にしたがって、使うときは出典「筆ポリゴンデータ（2026年度公開）」（農林水産省）と、加工したものであることを明記してください

## テーブル

| テーブル | 内容 |
| --- | --- |
| `fude.field` | 1 行が 1 区画（田か畑の 1 枚）。耕地の種類、農業集落コード、市区町村コード、重心の経緯度、形 |

## 使い方

東京都の市区町村ごとの田と畑の面積（ha）:

```sql
SELECT lg_code, land_type_name,
       count(*) AS fields,
       round(sum(ST_Area_Spheroid(ST_FlipCoordinates(geometry))) / 1e4) AS hectares
FROM maff.fude.field
WHERE city_code LIKE '13%'
GROUP BY ALL
ORDER BY hectares DESC;
```

農業集落コード（`agricultural_community_code`）で、農林業センサスの農業集落別の数字と結合できます。

## 収録範囲の注意

- 全国の 2026 年度公開データを収録しています
- 区画は航空写真・衛星画像を目視で判読して描いたもので、現地で確認したものではありません。土地の権利関係や筆界を示すものではなく、登記の筆（moj データセット）とは 1 対 1 になりません
- 田か畑かも写真の判読によるものです
- 区画の形は毎年描き直され、`polygon_uuid` は年度ごとに振り直されます
- 農業集落コードは区画の重心が入る農業集落です。先頭 5 桁が市区町村コードです

## 変換方法

都道府県ごとの分割 zip を取得して結合し、中の FlatGeobuf を DuckDB の spatial 拡張で読んで Parquet にします。全国で zip が 5.4GB あるため、都道府県ごとに Parquet にした直後に zip と FlatGeobuf を削除します。Parquet が既にある都道府県は取得し直しません。都道府県を絞るときは環境変数 `MAFF_PREFECTURES`（都道府県コードのカンマ区切り）を使います。

## ビルド

```bash
git submodule update --init
uv sync
scripts/build.sh                         # 全国
MAFF_PREFECTURES=13,14 scripts/build.sh  # 東京都と神奈川県だけ
```

Sync は手動実行だけです。
