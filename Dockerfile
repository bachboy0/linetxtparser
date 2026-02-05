FROM python:3.12-slim

# 解析ツールに必要な最小限のインフラ
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 依存ライブラリがある場合はここでインストール
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3"]
