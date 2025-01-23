import asyncio
import logging
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

class FileSystemHealthCheck:
    def __init__(self, storage_config):
        """
        ファイルシステムのヘルスチェックを行うクラス

        Args:
            storage_config: ストレージ設定オブジェクト
        """
        self.storage_paths = {
            type_name: config.path 
            for type_name, config in storage_config.items()
        }
        self._unhealthy_paths: Dict[str, bool] = {}

    async def start_health_check(self, check_interval: int = 60):
        """
        ヘルスチェックを開始します。

        Args:
            check_interval (int, optional): ヘルスチェックの間隔（秒）. デフォルトは60秒.
        """
        logger.info("ファイルシステムヘルスチェックを開始します")
        while True:
            await self._check_storage_health()
            await asyncio.sleep(check_interval)

    async def _check_storage_health(self):
        """
        各ストレージパスの健全性をチェックします
        """
        for type_name, path in self.storage_paths.items():
            try:
                # パスの存在と読み取り可能性を確認
                storage_path = Path(path)
                if not storage_path.exists():
                    raise OSError(f"パスが存在しません: {path}")
                
                # ディレクトリの場合はリストを試行
                if storage_path.is_dir():
                    list(storage_path.glob('*'))
                
                # 以前に障害状態だった場合は回復を通知
                if type_name in self._unhealthy_paths:
                    del self._unhealthy_paths[type_name]
                    logger.info(f"ストレージ {type_name} が復旧しました: {path}")
                
            except OSError as e:
                # 障害状態を記録
                if type_name not in self._unhealthy_paths:
                    logger.error(f"ストレージ {type_name} にアクセスできません: {e}")
                self._unhealthy_paths[type_name] = True

    def is_healthy(self, storage_type: str) -> bool:
        """
        特定のストレージタイプの健全性を確認します

        Args:
            storage_type (str): 確認するストレージの種類

        Returns:
            bool: ストレージが健全な場合はTrue、そうでない場合はFalse
        """
        return storage_type not in self._unhealthy_paths 