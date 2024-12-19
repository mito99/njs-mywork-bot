FROM python:3.11-slim

WORKDIR /app

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y \
  curl \
  && rm -rf /var/lib/apt/lists/*

# 依存関係ファイルをコピー
COPY pyproject.toml ./

# 依存関係のインストール
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN python -m venv $VIRTUAL_ENV && \
  pip install --no-cache-dir uv && \
  uv pip compile pyproject.toml -o requirements.txt && \
  uv pip install --no-cache -r requirements.txt

# アプリケーションのコピー
COPY src/ ./src/

# 環境変数の設定
ENV PYTHONPATH=/app

CMD ["python", "src/main.py"] 