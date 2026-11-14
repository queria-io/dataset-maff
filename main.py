"""農林水産省 筆ポリゴンのデータパイプライン。

1. fude: 都道府県ごとの分割 zip を取り、Parquet にする
2. dbt: dbt ビルド
"""

import logging

from dbt.cli.main import dbtRunner

from pipelines import plans
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
    logger.info("1/3: fude (筆ポリゴン)")
    download_fude()

    logger.info("2/3: plans (行政事業レビューが挙げる計画・通知等)")
    plans.download_plans()
    plans.build_plans_parquet()

    logger.info("3/3: dbt build")
    dbt_build()


if __name__ == "__main__":
    main()
