import logging
from datetime import datetime
from typing import ClassVar

from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)

class GetCurrentDateTimeTool(BaseTool):
    """
    現在の日時を指定されたフォーマットで返却します。
    """
    
    name: ClassVar[str] = "get_current_datetime"
    description: ClassVar[str] = "現在の日時を「yyyy-MM-dd(曜日) HH:mm:ss」形式で返却します"
    
    def _run(self) -> str:
        """
        現在の日時を「yyyy-MM-dd(曜日) HH:mm:ss」形式で返却します。

        Returns:
            str: フォーマットされた現在日時の文字列

        Note:
            - 日時は常にローカルタイムゾーンで返却されます
            - 曜日は日本語で表示されます（例：月、火、水...）
        """
        weekday_jp = ["月", "火", "水", "木", "金", "土", "日"]
        now = datetime.now()
        weekday = weekday_jp[now.weekday()]
        
        logger.info("GetCurrentDateTimeTool: getting current datetime with weekday")
        return now.strftime(f"%Y-%m-%d({weekday}) %H:%M:%S") 