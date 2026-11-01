"""農林水産省 筆ポリゴンのデータパイプライン。

1. fude: 都道府県ごとの分割 zip を取り、Parquet にする
2. dbt: dbt ビルド
"""

import logging

from dbt.cli.main import dbtRunner

from pipelines.fude import download_fude

# dbt を読み込むとルートロガーが先に設定されるので、force で上書きする
logging.basicConfig(level=logging.INFO, format="%(message)s", force=True)
logger = logging.getLogger("pipelines")


def dbt_build():
    dbt = dbtRunner()
    for command in (["deps"], ["build"], ["docs", "generate"]):
        result = dbt.invoke(command)
        if not result.success:
            raise SystemExit(f"dbt {' '.join(command)} failed")


def main():
    logger.info("1/2: fude (筆ポリゴン)")
    download_fude()

    logger.info("2/2: dbt build")
    dbt_build()


if __name__ == "__main__":
    main()
