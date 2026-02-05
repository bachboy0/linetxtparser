#!/usr/bin/env python3
import json

# 残っている純粋な「画像」メッセージの位置を確認
with open("output/target1.jsonl", "r", encoding="utf-8") as f:
    messages = [json.loads(line) for line in f]

# 「画像」のみのメッセージを確認
pure_image_msgs = [m for m in messages if m["message"].strip() == "画像"]
print(f"純粋な「画像」メッセージ数: {len(pure_image_msgs)}")
for msg in pure_image_msgs:
    print(f"{msg['date']} {msg['time']} {msg['user']}: '{msg['message']}'")
    print(f"  長さ: {len(msg['message'])}, repr: {repr(msg['message'])}")
