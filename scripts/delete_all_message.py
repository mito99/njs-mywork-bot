import asyncio

from slack_sdk.errors import SlackApiError
from slack_sdk.web.async_client import AsyncWebClient


async def delete_thread_messages(client: AsyncWebClient, channel_id: str, thread_ts: str):
    """スレッド内のメッセージを削除する

    Args:
        client (AsyncWebClient): Slackクライアント
        channel_id (str): チャネルID
        thread_ts (str): スレッドの親メッセージのタイムスタンプ
    """
    try:
        # スレッド内のメッセージを取得
        result = await client.conversations_replies(
            channel=channel_id,
            ts=thread_ts
        )
        
        if not result["ok"]:
            print(f"Error fetching thread messages: {result['error']}")
            return
            
        # スレッド内の各メッセージを削除
        for msg in result.get("messages", []):
            try:
                await client.chat_delete(
                    channel=channel_id,
                    ts=msg["ts"]
                )
                print(f"Deleted thread message: {msg['ts']}")
                await asyncio.sleep(1)
            except SlackApiError as e:
                print(f"Error deleting thread message {msg['ts']}: {e.response['error']}")

    except SlackApiError as e:
        print(f"Error fetching thread: {e.response['error']}")

async def delete_all_messages(channel_id: str, token: str):
    """指定されたチャネル内の全メッセージを削除する

    Args:
        channel_id (str): メッセージを削除するチャネルのID
        token (str): Slackのボットトークン
    """
    client = AsyncWebClient(token=token)
    
    try:
        # メッセージの取得と削除を繰り返す
        cursor = None
        while True:
            # チャネル履歴を取得
            result = await client.conversations_history(
                channel=channel_id,
                cursor=cursor,
                limit=100  # 一度に取得するメッセージ数
            )
            
            if not result["ok"]:
                print(f"Error fetching messages: {result['error']}")
                break
                
            messages = result.get("messages", [])
            if not messages:
                break
                
            # 各メッセージを削除
            for msg in messages:
                # スレッドの親メッセージの場合、スレッド内のメッセージも削除
                if msg.get("thread_ts") == msg.get("ts"):
                    await delete_thread_messages(client, channel_id, msg["ts"])
                
                try:
                    await client.chat_delete(
                        channel=channel_id,
                        ts=msg["ts"]
                    )
                    print(f"Deleted message: {msg['ts']}")
                    await asyncio.sleep(1)
                except SlackApiError as e:
                    print(f"Error deleting message {msg['ts']}: {e.response['error']}")
            
            # 次のページがあるか確認
            cursor = result.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
            
        print("Message deletion completed")
        
    except SlackApiError as e:
        print(f"Error: {e.response['error']}")

async def main():
    # 環境変数から設定を読み込む
    import os

    from dotenv import load_dotenv
    
    load_dotenv()
    
    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
    SLACK_USER_TOKEN = os.getenv("SLACK_USER_TOKEN")
    
    if not SLACK_BOT_TOKEN:
        print("Please set SLACK_BOT_TOKEN in .env file")
        exit(1)
        
    if not SLACK_USER_TOKEN:
        print("Please set SLACK_USER_TOKEN in .env file")
        exit(1)
    
    # ユーザーにチャンネルIDの入力を求める
    #channel_id = input("削除対象のチャンネルIDを入力してください: ")
    channel_id = os.getenv("SLACK_ROBOT_CHANNEL_ID")
    
    # 入力確認
    confirm = input(f"チャンネル {channel_id} のメッセージをすべて削除します。よろしいですか？(y/N): ")
    if confirm.lower() != 'y':
        print("処理を中止しました。")
        exit(0)
    
    # BOTメッセージの削除
    await delete_all_messages(channel_id, SLACK_BOT_TOKEN)
    
    # ユーザーメッセージの削除
    await delete_all_messages(channel_id, SLACK_USER_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
