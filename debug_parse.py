#!/usr/bin/env python3
"""
デバッグ用:「画像」メッセージの処理を確認
"""

import re
import json
from pathlib import Path

DATE_PATTERN = re.compile(r"^(\d{4}\.\d{2}\.\d{2})\s+(.+曜日)$")
MESSAGE_PATTERN = re.compile(r"^(\d{2}:\d{2})\s+(.+)$")

current_date = None
current_time = None
line_num = 0

# 742-746行を読む（ロキシーの画像メッセージ）
with open("targets/target1.txt", "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        if 740 <= i <= 750:
            line = line.rstrip("\n\r")
            print(f"Line {i}: '{line}'")

            date_match = DATE_PATTERN.match(line)
            if date_match:
                current_date = date_match.group(1)
                print(f"  -> 日付: {current_date}")
                continue

            msg_match = MESSAGE_PATTERN.match(line)
            if msg_match:
                current_time = msg_match.group(1)
                rest = msg_match.group(2)
                parts = rest.split(None, 1)
                if len(parts) == 2:
                    user, message = parts[0], parts[1]
                else:
                    user, message = parts[0], ""
                print(f"  -> メッセージ: {current_time} {user} '{message}'")
                print(f"     除外?: {message.strip() == '画像'}")
