# ビルドと更新

データセットの概要は [README.md](README.md) にあります。ここにはこのリポジトリでデータセットをビルド・更新する手順を書きます。

## ビルド

```bash
git submodule update --init
uv sync
scripts/build.sh                         # 全国
MAFF_PREFECTURES=13,14 scripts/build.sh  # 東京都と神奈川県だけ
```

Sync は手動実行だけです。
