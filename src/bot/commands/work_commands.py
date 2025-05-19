import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime

import requests

from bot.config import Config
from bot.tools.work_tools.attendance import UpdateAttendanceSheetTool
from bot.tools.work_tools.types import FileType
from bot.utils.message import MessageSender

logger = logging.getLogger(__name__)

class WorkCommand(ABC):
    """作業コマンドの抽象基底クラス"""

    @abstractmethod
    async def execute(self, client, message, say):
        """コマンドを実行する抽象メソッド"""
        pass

    @classmethod
    async def create(cls, command_text: str, config: Config) -> "WorkCommand":
        """コマンドに応じたコマンドを返すビルダーメソッド"""

        # コマンドテキストをスペースで分割
        parts = command_text.split()
        action = parts[0].upper() if len(parts) > 0 else None
        file_type = parts[1] if len(parts) > 1 else None
        file_name = parts[2] if len(parts) > 2 else None

        storage_types = list(config.application.storage.keys())
        if file_type not in storage_types:
            return UsageCommand(config)

        if action == "GET":
            if not file_name:
                return UsageCommand(config)
            return GetFileCommand(file_type, file_name, config)
        elif action == "LIST":
            return ListFileCommand(file_type, config)
        elif action == "PUT":
            return PutFileCommand(file_type, config)
        elif action == "DELETE":
            return DeleteFileCommand(file_type, file_name, config)
        elif action == "UPDATE":
            if not file_name:
                return UsageCommand(config)
            if file_type == FileType.ATTENDANCE.value:
                return UpdateAttendanceCommand(file_type, file_name, config)
            elif file_type == FileType.HOLIDAY.value:
                return UpdatePaidLeaveCommand(file_type, file_name, config)

        return UsageCommand(config)


class DeleteFileCommand(WorkCommand):
    """ファイルを削除するコマンド"""

    def __init__(self, file_type: str, file_name: str, config: Config):
        self.file_type = file_type
        self.file_name = file_name
        self.config = config

    async def execute(self, client, message, say):
        """ファイルを削除します。"""
        thread_ts = message.get("ts")
        send_message = MessageSender(client, message["channel"], thread_ts)
        try:
            await send_message.send(f"{self.file_type}ファイルの削除を開始します...")
            storage_path = self.config.application.storage[self.file_type].path
            file_path = os.path.join(storage_path, self.file_name)
            os.remove(file_path)
            await send_message.send(f"✅ {self.file_type}ファイルを削除しました。=> {file_path}")
        except Exception as e:
            logger.error(f"ファイルの削除に失敗しました。エラー: {e}")
            await send_message.send(f"❌ ファイルの削除に失敗しました。エラー: {e}")
        return


class UsageCommand(WorkCommand):
    """使用方法を表示するコマンド"""

    def __init__(self, config: Config):
        self.config = config

    async def execute(self, client, message, say):
        """使用方法を表示します。"""
        usage_message = (
            "使用可能なコマンド:\n"
            "- `cmd get <ストレージ名> <ファイル名>`: ファイルを取得\n"
            "- `cmd put <ストレージ名>`: ファイルをアップロード\n"
            "- `cmd list <ストレージ名>`: ファイル一覧を表示\n"
            "- `cmd delete <ストレージ名> <ファイル名>`: ファイルを削除\n"
            "- `cmd update 勤怠 <ファイル名>`: 勤怠表を更新\n"
            "- `cmd update 有休 <ファイル名>`: 有給休暇ファイルを更新\n\n"
            "利用可能なストレージ名:\n"
            + "\n".join([f"- {storage.value}" for storage in FileType])
        )
        await say(f"使用方法:\n{usage_message}")


class GetFileCommand(WorkCommand):
    """ファイルを取得するコマンド"""

    def __init__(self, file_type: str, work_file_name: str, config: Config):
        self.file_type = file_type
        self.storage_path = config.application.storage[file_type].path
        self.file_path = os.path.join(self.storage_path, work_file_name)

    async def execute(self, client, message, say):
        """ファイルをアップロードします。"""
        thread_ts = message.get("ts")
        send_message = MessageSender(client, message["channel"], thread_ts)
        try:
            await send_message.send(f"{self.file_type}ファイルの取得を開始します...")
            await client.files_upload_v2(
                channel=message["channel"],
                file=self.file_path,
                filename=os.path.basename(self.file_path),
                initial_comment=f"{self.file_type}ファイルを送ります。",
                thread_ts=thread_ts
            )
            await send_message.send("✅ ファイルの取得が完了しました")
        except Exception as e:
            logger.error(f"ファイルの取得に失敗しました。エラー: {e}")
            await send_message.send(f"❌ ファイルの取得に失敗しました。エラー: {e}")
        return


class ListFileCommand(WorkCommand):
    """ファイル一覧を取得するコマンド"""

    def __init__(self, file_type: str, config: Config):
        self.file_type = file_type
        self.storage_path = config.application.storage[file_type].path

    async def execute(self, client, message, say):
        """ファイル一覧を取得します。"""
        thread_ts = message.get("ts")
        send_message = MessageSender(client, message["channel"], thread_ts)
        try:
            await send_message.send(f"{self.file_type}ファイル一覧の取得を開始します...")
            file_list = os.listdir(self.storage_path)
            if len(file_list) == 0:
                await send_message.send(f"ℹ️ {self.file_type}ファイルはありません。")
                return

            file_list_str = "\n".join([f"・{file}" for file in file_list])
            await send_message.send(f"✅ {self.file_type}ファイル一覧:\n{file_list_str}")
        except Exception as e:
            logger.error(f"ファイル一覧の取得に失敗しました。エラー: {e}")
            await send_message.send(f"❌ ファイル一覧の取得に失敗しました。エラー: {e}")
        return


class PutFileCommand(WorkCommand):
    """ファイルを置くコマンド"""

    def __init__(self, file_type: str, config: Config):
        self.file_type = file_type
        self.storage_path = config.application.storage[file_type].path
        self.slack_bot_token = config.slack_bot_task.bot_token

    async def execute(self, client, message, say):
        """ファイルを置きます。"""
        thread_ts = message.get("ts")
        send_message = MessageSender(client, message["channel"], thread_ts)
        try:
            await send_message.send(f"{self.file_type}ファイルのアップロードを開始します...")
            if message.get("files") and len(message["files"]) <= 0:
                await send_message.send("❌ ファイルがありません。")
                return

            file = message["files"][0]
            file_url = file.get("url_private_download")
            if not file_url:
                await send_message.send("❌ ファイルのURLが取得できません。")
                return

            filename = file.get("name")
            save_path = os.path.join(self.storage_path, filename)

            headers = {"Authorization": f"Bearer {self.slack_bot_token}"}
            response = requests.get(file_url, headers=headers)
            with open(save_path, "wb") as f:
                f.write(response.content)

            await send_message.send(f"✅ {self.file_type}ファイルを置きました。=> {save_path}")
        except Exception as e:
            logger.error(f"ファイルのアップロードに失敗しました。エラー: {e}")
            await send_message.send(f"❌ ファイルのアップロードに失敗しました。エラー: {e}")
        return


class UpdateAttendanceCommand(WorkCommand):
    """勤怠表を更新するコマンド"""

    def __init__(self, file_type: str, file_name: str, config: Config):
        self.file_type = file_type
        self.file_name = file_name
        self.config = config

    async def _get_user_info(self, client, message, say):
        # ユーザーIDを取得
        user_id = message.get("user")
        if not user_id:
            raise ValueError("ユーザーIDが取得できません。")
        
        user_info = await client.users_info(user=user_id)
        if not user_info["ok"]:
            raise ValueError("ユーザー情報の取得に失敗しました。")
        return user_info


    async def execute(self, client, message, say):
        """勤怠表を更新します。"""
        
        thread_ts = message.get("ts")
        send_message = MessageSender(client, message["channel"], thread_ts)
        try:
            # 初期メッセージを送信
            await send_message.send(
                "勤怠表の更新を開始します..."
            )

            # ユーザー情報の取得
            await send_message.send(
                "ユーザー情報を取得中..."
            )
            user_info = await self._get_user_info(client, message, say)
            user_name = user_info["user"]["real_name"]
            await send_message.send(
                f"✅ ユーザー情報を取得しました: {user_name}"
            )

            # ファイルの存在確認
            storage_path = self.config.application.storage[self.file_type].path
            file_path = os.path.join(storage_path, self.file_name)
            if not os.path.exists(file_path):
                files = os.listdir(storage_path)
                file_list = "\n".join(files)
                await send_message.send(
                    f"❌ 勤怠ファイル {self.file_name} が見つかりません。\n\n現在のファイル一覧:\n{file_list}"
                )
                return None

            # 勤怠表の更新
            await send_message.send(
                "勤怠表の更新を開始します..."
            )
            
            now = datetime.now()
            update_month = now.month

            tool = UpdateAttendanceSheetTool(self.config, client, message)
            await tool._arun(
                user_name=user_name,
                update_year=None,
                update_month=update_month,
                attendance_file_name=self.file_name
            )

            await send_message.send(
                "✅ 勤怠表の更新が完了しました"
            )

        except Exception as e:
            logger.error(f"勤怠表の更新に失敗しました。エラー: {e}")
            await send_message.send(
                f"❌ 勤怠表の更新に失敗しました。エラー: {e}"
            )
        return 


class UpdatePaidLeaveCommand(WorkCommand):
    """有給休暇ファイルを更新するコマンド"""

    def __init__(self, file_type: str, file_name: str, config: Config):
        self.file_type = file_type
        self.file_name = file_name
        self.config = config

    async def _get_user_info(self, client, message, say):
        # ユーザーIDを取得
        user_id = message.get("user")
        if not user_id:
            raise ValueError("ユーザーIDが取得できません。")
        
        user_info = await client.users_info(user=user_id)
        if not user_info["ok"]:
            raise ValueError("ユーザー情報の取得に失敗しました。")
        return user_info

    async def execute(self, client, message, say):
        """有給休暇ファイルを更新します。"""
        thread_ts = message.get("ts")
        send_message = MessageSender(client, message["channel"], thread_ts)
        try:
            # 初期メッセージを送信
            await send_message.send(
                "有給休暇ファイルの更新を開始します..."
            )

            # ユーザー情報の取得
            await send_message.send(
                "ユーザー情報を取得中..."
            )
            user_info = await self._get_user_info(client, message, say)
            user_name = user_info["user"]["real_name"]
            await send_message.send(
                f"✅ ユーザー情報を取得しました: {user_name}"
            )

            # ファイルの存在確認
            storage_path = self.config.application.storage[self.file_type].path
            file_path = os.path.join(storage_path, self.file_name)
            if not os.path.exists(file_path):
                files = os.listdir(storage_path)
                file_list = "\n".join(files)
                await send_message.send(
                    f"❌ 有給休暇ファイル {self.file_name} が見つかりません。\n\n現在のファイル一覧:\n{file_list}"
                )
                return None

            # 有給休暇ファイルの更新
            await send_message.send(
                "有給休暇ファイルの更新を開始します..."
            )
            
            now = datetime.now()
            update_month = now.month

            from bot.tools.work_tools.paid_leave import UpdatePaidLeaveTool
            tool = UpdatePaidLeaveTool(self.config, client, message)
            await tool._arun(
                user_name=user_name,
                update_year=None,
                update_month=update_month,
                paid_leave_file_name=self.file_name
            )

            await send_message.send(
                "✅ 有給休暇ファイルの更新が完了しました"
            )

        except Exception as e:
            logger.error(f"有給休暇ファイルの更新に失敗しました。エラー: {e}")
            await send_message.send(
                f"❌ 有給休暇ファイルの更新に失敗しました。エラー: {e}"
            )
        return 
