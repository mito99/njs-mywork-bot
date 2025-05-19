"""
ファイル名の制約を管理するモジュール
"""
import re
from typing import List

from bot.config import Config


class FileRestriction:
    """
    ファイル名の制約を管理するクラス
    """

    def __init__(self, config: Config) -> None:
        """
        初期化

        Args:
            is_enabled (bool): 制約の有効/無効
        """
        self._is_enabled = config.njs_file_access_restriction_enabled
        self._patterns = self._parse_patterns(config.njs_file_name_pattern_restriction)

    def _parse_patterns(self, pattern_string: str) -> List[re.Pattern]:
        """
        正規表現パターン文字列をパースしてre.Patternのリストに変換

        Args:
            pattern_string (str): カンマ区切りの正規表現パターン

        Returns:
            List[re.Pattern]: コンパイル済みの正規表現パターンのリスト
        """
        if not pattern_string:
            return []
        return [re.compile(pattern.strip()) for pattern in pattern_string.split(",")]

    def is_allowed(self, file_path: str) -> bool:
        """
        指定されたファイルパスが制約に適合するか判定

        Args:
            file_path (str): 判定対象のファイルパス

        Returns:
            bool: 制約に適合する場合はTrue、それ以外はFalse
        """
        # 制約が無効な場合は常に許可
        if not self._is_enabled:
            return True

        # パターンが未設定の場合は常に許可
        if not self._patterns:
            return True

        # いずれかのパターンにマッチするかチェック
        return any(pattern.search(file_path) for pattern in self._patterns) 