#!/usr/bin/env python3
import json
from pathlib import Path

# 全てのJSONLファイルをチェック
output_dir = Path("output")
for jsonl_file in sorted(output_dir.glob("*.jsonl")):
    with open(jsonl_file, "r", encoding="utf-8") as f:
        messages = [json.loads(line) for line in f]

    # 「画像」のみのメッセージをチェック
    pure_image = [m for m in messages if m["message"].strip() == "画像"]

    # 「画像」を含むメッセージもチェック（参考情報）
    contains_image = [m for m in messages if "画像" in m["message"]]

    print(f"{jsonl_file.name}:")
    print(f"  総メッセージ数: {len(messages)}")
    print(f"  純粋な「画像」メッセージ: {len(pure_image)}")
    print(f"  「画像」を含むメッセージ: {len(contains_image)}")
    if contains_image:
        print(f"    例: {contains_image[0]['message'][:50]}...")
    print()
