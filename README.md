# Slack Assistant Bot

Slack ワークスペース用のアシスタントボットです。ファイル管理、メッセージ処理、そして Gemini Pro を活用した自然な対話機能を提供し、チームの生産性向上を支援します。

## 機能

- **ファイル管理**:
  - アップロード: Slack に投稿されたファイルを指定のストレージへ保存します。
  - ダウンロード: ストレージに保存されたファイルを Slack へ送信します。
  - 一覧表示: 指定ストレージ内のファイルリストを Slack 上で確認できます。
  - 削除: 不要になったファイルをストレージから削除します。
- **メッセージ対応**:
  - 自動応答: 設定されたキーワードやパターンに対して自動的に応答します。
  - Gemini Pro連携: 自然言語による質問応答やテキスト生成が可能です。
- **セキュアなファイル保存**:
  - ローカルファイルシステムに安全にファイルを保管します。
- **コマンド操作**:
  - `list <ストレージ名>`: 指定したストレージのファイル一覧を表示します。
  - `get <ストレージ名> <ファイル名>`: 指定したストレージからファイルをダウンロードします。
  - `put <ストレージ名>`:  Slack にアップロードされたファイルを指定ストレージに保存します。
  - `delete <ストレージ名> <ファイル名>`: 指定したストレージからファイルを削除します。

## セットアップ

### 1. 環境構築

#### 前提条件

- Python 3.11 以上
- Docker
- Docker Compose

#### 手順

1. リポジトリをクローンします。
   ```bash
   git clone <リポジトリの URL>
   cd <リポジトリ名>
   ```

2. 環境変数を設定します。 `.env.example` をコピーして `.env` ファイルを作成し、必要な環境変数を記述してください。
   ```bash
   cp .env.example .env
   ```
   .env ファイルに必要な環境変数は以下の通りです。

   ```
   SLACK_BOT_TOKEN=あなたの Slack Bot トークン
   SLACK_APP_TOKEN=あなたの Slack App トークン
   SLACK_SIGNING_SECRET=あなたの Slack Signing Secret
   GOOGLE_API_KEY=あなたの Google API キー
   ```

3. 設定ファイルを作成します。 `config.yaml` にアプリケーションの設定を記述します。
   ```yaml:config.yaml
   application:
     log_level: INFO

     slack:
       allowed_users:
         - Uxxxxxxxx  # 操作を許可するユーザーID

     storage:
       "勤怠":
         path: ./storage/work_report
       "有休":
         path: ./storage/paid_leave
   ```

4. Docker Compose でアプリケーションを起動します。
   ```bash
   docker compose up -d --build
   ```

### 2. Slack アプリの設定

1. **Bot ユーザーの作成**: Slack ワークスペースに新しい Bot ユーザーを作成し、Bot トークンを取得します。
2. **App トークンの取得**: Slack アプリケーションを作成し、Socket Mode を有効にして App レベルトークンを取得します。
3. **Signing Secret の設定**: Slack アプリの Basic Information ページから Signing Secret を取得します。
4. **権限設定**: Slack アプリの OAuth & Permissions ページで必要な権限（`files:read`, `files:write`, `chat:write`, `users:read`)を設定し、ワークスペースにインストールします。

## 使い方

Slack で以下のコマンドを Bot に送信することで操作できます。

- **ファイルのアップロード**:
  1. ファイルを Slack にアップロードします。
  2. `@bot名 put <ストレージ名>` というメッセージを送信します。例: `@アシスタント put 勤怠`

- **ファイルのダウンロード**:
  ```
  @bot名 get <ストレージ名> <ファイル名>
  ```
  例: `@アシスタント get 勤怠 report.csv`

- **ファイルの一覧表示**:
  ```
  @bot名 list <ストレージ名>
  ```
  例: `@アシスタント list 勤怠`

- **ファイルの削除**:
  ```
  @bot名 delete <ストレージ名> <ファイル名>
  ```
  例: `@アシスタント delete 勤怠 old_report.csv`

## 開発

### 開発環境の構築

1. Poetry をインストールします。
   ```bash
   pip install poetry
   ```

2. 依存関係をインストールします。
   ```bash
   poetry install
   ```

### 依存関係の管理

依存関係の追加は `uv add` コマンドを使用します。
