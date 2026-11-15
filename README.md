# dataset-maff

Queria のデータセット `maff`（農林水産省 筆ポリゴン（農地の区画））のリポジトリです。データセットの説明は [docs/index.md](docs/index.md) にあります。

## ビルド

```bash
git submodule update --init
uv sync
scripts/build.sh                         # 全国
MAFF_PREFECTURES=13,14 scripts/build.sh  # 東京都と神奈川県だけ
```

Sync は手動実行だけです。
