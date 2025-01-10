import os
from typing import Optional

import boto3
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_aws import ChatBedrock
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

def init_bedrock_chat() -> ChatBedrock:
    """AWS Bedrockのチャットモデルを初期化します"""

    return ChatBedrock(
        model_id=os.getenv("AWS_MODEL_ID"),
        model_kwargs={
            "max_tokens": 4096,
            "temperature": 0,
            "top_p": 1,
        }
    )

def summarize_email(email_content: str, max_length: Optional[int] = None) -> str:
    """メールの内容を要約します

    Args:
        email_content (str): 要約するメールの内容
        max_length (Optional[int], optional): 要約の最大文字数. デフォルトはNone.

    Returns:
        str: 要約された内容
    """
    # テキストを分割
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=4000,
        chunk_overlap=200,
        length_function=len,
    )
    texts = text_splitter.split_text(email_content)

    # LLMの初期化
    chat = init_bedrock_chat()

    # システムプロンプトとユーザーメッセージを作成
    system_message = SystemMessage(
        "メールの内容をSlack通知用に最適化して圧縮するプロンプトです。\n\n"
        "入力：\n"
        "- メールの本文\n"
        "- メールのメタデータ（件名、送信者、送信日時）\n"
        "- 添付ファイルの情報（存在する場合）\n\n"
        "要件：\n"
        "1. 文字数制限：\n"
        "- 本文は100文字以内に圧縮\n"
        "- 超過する場合は重要度の高い情報を優先\n\n"
        "2. 必ず含めるべき情報：\n"
        "- メールの主題\n"
        "- 重要な日付や締切\n"
        "- 具体的な数値やデータ\n"
        "- アクションアイテム（もしあれば）\n\n"
        "3. 出力フォーマット：\n"
        "📧 [件名]\n"
        "From: [送信者] | 📅 [送信日時]\n"
        "[圧縮された本文]\n"
        "📎 添付: [ファイル名（あれば）]\n\n"
        "4. 圧縮のガイドライン：\n"
        "- 冗長な表現や挨拶文を削除\n"
        "- 箇条書きを活用して情報を整理\n"
        "- 重要なキーワードは保持\n"
        "- 文脈を維持しながら簡潔に表現\n\n"
        "例：\n"
        "入力メール：\n"
        "お世話になっております。先日お願いしておりました第3四半期の売上レポートについて、"
        "添付ファイルにてお送りさせていただきます。内容をご確認いただき、特に5ページ目の新規顧客獲得施策について、"
        "来週月曜日までにフィードバックをいただけますと幸いです。よろしくお願いいたします。"
        "\n\n"
        "出力：\n"
        "📧 第3四半期売上レポートの送付\n"
        "From: 営業部 山田太郎 | 📅 2024/1/10 15:30\n"
        "・Q3売上レポート送付済\n"
        "・新規顧客獲得施策（P.5）要フィードバック\n"
        "・期限：1/15（月）\n"
        "📎 添付: Q3_sales_report.pdf\n"
    )
    
    # 各チャンクを要約
    summaries = []
    for text in texts:
        messages = [
            system_message,
            HumanMessage(content=f"以下のメールを要約してください:\n\n{text}")
        ]
        response = chat.invoke(messages)
        summaries.append(response.content)

    # 複数の要約を結合
    final_summary = " ".join(summaries)

    if max_length and len(final_summary) > max_length:
        final_summary = final_summary[:max_length] + "..."

    return final_summary

def main():
    # サンプルのメール内容
    sample_email = """
    件名: プロジェクト進捗報告会について

    チームの皆様

    お疲れ様です。プロジェクトマネージャーの山田です。
    来週のプロジェクト進捗報告会について、以下の通りご連絡いたします。

    日時: 2024年2月20日（火）14:00-16:00
    場所: 会議室A（オンライン参加も可能）
    議題:
    1. 各チームの進捗報告（30分）
    2. 課題の共有と解決策の検討（45分）
    3. 次期フェーズの計画確認（30分）
    4. 質疑応答（15分）

    参加者の皆様には、事前に進捗報告資料の提出をお願いいたします。
    提出期限は2024年2月19日（月）17:00までとさせていただきます。

    また、オンライン参加を希望される方は、前日までに私までご連絡ください。
    接続情報は、当日の朝にお送りいたします。

    ご質問等ございましたら、お気軽にご連絡ください。
    よろしくお願いいたします。

    山田太郎
    プロジェクトマネージメント部
    """

    # メールの要約を実行
    summary = summarize_email(sample_email, max_length=200)
    print("要約結果:")
    print(summary)

if __name__ == "__main__":
    main() 