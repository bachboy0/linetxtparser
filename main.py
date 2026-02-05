#!/usr/bin/env python3
"""
LINEトーク履歴をJSONL形式でパースするスクリプト
"""

import re
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any


class LineParser:
    """LINEトーク履歴のパーサー"""

    # 日付行のパターン: "2026.01.09 金曜日"
    DATE_PATTERN = re.compile(r"^(\d{4}\.\d{2}\.\d{2})\s+(.+曜日)$")

    # メッセージ行のパターン: "01:54 ユーザー名 メッセージ"
    MESSAGE_PATTERN = re.compile(r"^(\d{2}:\d{2})\s+(.+)$")

    # LINEシステムメッセージのパターン（ユーザー名とメッセージを分離するため）
    SYSTEM_ACTIONS = [
        "がメッセージの送信を取り消しました",
        "がアルバムに写真を追加しました",
        "がノートを作成しました",
        "が通話をかけました",
        "が退出しました",
        "が参加しました",
    ]

    # メッセージ内容でよく使われる単語（ユーザー名ではない）
    NON_USERNAME_KEYWORDS = [
        "開演",
        "開場",
        "終",
        "開始",
        "終了",
        "開催",
        "中止",
        "延期",
    ]

    def __init__(self):
        self.current_date: Optional[str] = None
        self.current_day: Optional[str] = None
        self.current_message: Optional[Dict[str, Any]] = None
        self.excluded_count: int = 0

    def _is_valid_message_line(self, text: str) -> bool:
        """
        時刻パターンの後のテキストが実際にメッセージ行（ユーザー名を含む）かどうかを判定

        Args:
            text: 時刻の後のテキスト部分

        Returns:
            True: 有効なメッセージ行, False: メッセージの続き
        """
        if not text.strip():
            return False

        # 最初の単語を取得
        first_word = text.split()[0] if text.split() else ""

        # メッセージ内容でよく使われる単語で始まる場合は、メッセージの続きと判定
        for keyword in self.NON_USERNAME_KEYWORDS:
            if first_word.startswith(keyword):
                return False

        # それ以外は有効なメッセージ行として扱う
        return True

    def _should_exclude_message(self, message: Dict[str, Any]) -> bool:
        """
        メッセージを除外すべきかどうかを判定

        Args:
            message: メッセージデータ

        Returns:
            True: 除外すべき, False: 含めるべき
        """
        # 「画像」のみのメッセージは除外
        return message.get("message", "").strip() == "画像"

    def _split_user_message(self, text: str) -> tuple[str, str]:
        """
        ユーザー名とメッセージを分離する

        Args:
            text: "ユーザー名 メッセージ" または "ユーザー名がメッセージの送信を取り消しました" 形式のテキスト

        Returns:
            (ユーザー名, メッセージ) のタプル
        """
        # システムメッセージのパターンをチェック
        for action in self.SYSTEM_ACTIONS:
            if action in text:
                # actionの前の部分がユーザー名
                idx = text.find(action)
                user = text[:idx]
                message = action
                return user, message

        # 通常のメッセージ: 最初の空白で分割
        parts = text.split(None, 1)  # 最大1回分割
        if len(parts) == 2:
            return parts[0], parts[1]
        elif len(parts) == 1:
            # メッセージなし（例: "画像"のみ）
            return parts[0], ""
        else:
            return text, ""

    def parse_file(self, input_path: str, output_path: str) -> None:
        """
        ファイルをパースしてJSONL形式で出力

        Args:
            input_path: 入力ファイルパス
            output_path: 出力ファイルパス
        """
        with open(input_path, "r", encoding="utf-8") as infile, open(
            output_path, "w", encoding="utf-8"
        ) as outfile:

            for line in infile:
                line = line.rstrip("\n\r")

                # 空行はスキップ
                if not line.strip():
                    continue

                # 日付行のチェック
                date_match = self.DATE_PATTERN.match(line)
                if date_match:
                    # 前のメッセージがあれば出力（除外対象でない場合のみ）
                    if self.current_message:
                        if self._should_exclude_message(self.current_message):
                            self.excluded_count += 1
                        else:
                            outfile.write(
                                json.dumps(self.current_message, ensure_ascii=False)
                                + "\n"
                            )
                        self.current_message = None

                    self.current_date = date_match.group(1)
                    self.current_day = date_match.group(2)
                    continue

                # メッセージ行のチェック
                message_match = self.MESSAGE_PATTERN.match(line)
                if message_match:
                    time = message_match.group(1)
                    rest = message_match.group(2)

                    # 実際にメッセージ行かどうかをチェック
                    if self._is_valid_message_line(rest):
                        # 前のメッセージがあれば出力（除外対象でない場合のみ）
                        if self.current_message:
                            if self._should_exclude_message(self.current_message):
                                self.excluded_count += 1
                            else:
                                outfile.write(
                                    json.dumps(self.current_message, ensure_ascii=False)
                                    + "\n"
                                )

                        # ユーザー名とメッセージを分離
                        user, message = self._split_user_message(rest)

                        # 新しいメッセージを作成
                        self.current_message = {
                            "date": self.current_date,
                            "day": self.current_day,
                            "time": time,
                            "user": user,
                            "message": message,
                        }
                    else:
                        # メッセージの続き（時刻パターンにマッチしたが、ユーザー名ではない）
                        if self.current_message:
                            # 既存のメッセージに追加
                            if self.current_message["message"]:
                                self.current_message["message"] += "\n" + line
                            else:
                                self.current_message["message"] = line
                else:
                    # メッセージの続き（複数行）
                    if self.current_message:
                        # 既存のメッセージに追加
                        if self.current_message["message"]:
                            self.current_message["message"] += "\n" + line
                        else:
                            self.current_message["message"] = line

            # 最後のメッセージを出力（除外対象でない場合のみ）
            if self.current_message:
                if self._should_exclude_message(self.current_message):
                    self.excluded_count += 1
                else:
                    outfile.write(
                        json.dumps(self.current_message, ensure_ascii=False) + "\n"
                    )


def main():
    """メイン処理"""
    parser = LineParser()

    # targetsディレクトリ内のすべてのtxtファイルを処理
    targets_dir = Path("targets")

    if not targets_dir.exists():
        print(f"Error: {targets_dir} ディレクトリが見つかりません", file=sys.stderr)
        sys.exit(1)

    txt_files = list(targets_dir.glob("*.txt"))

    if not txt_files:
        print(
            f"Warning: {targets_dir} 内にtxtファイルが見つかりません", file=sys.stderr
        )
        sys.exit(0)

    # 出力ディレクトリを作成
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    total_messages = 0
    total_excluded = 0

    # 各ファイルを処理
    for txt_file in txt_files:
        print(f"Processing: {txt_file}")
        output_file = output_dir / f"{txt_file.stem}.jsonl"

        try:
            parser_instance = LineParser()  # 各ファイルごとに新しいパーサーを作成
            parser_instance.parse_file(str(txt_file), str(output_file))

            # 出力されたメッセージ数をカウント
            with open(output_file, "r", encoding="utf-8") as f:
                count = sum(1 for _ in f)
                total_messages += count
                total_excluded += parser_instance.excluded_count

            print(
                f"  -> Output: {output_file} ({count} messages, {parser_instance.excluded_count} excluded)"
            )
        except Exception as e:
            print(f"Error processing {txt_file}: {e}", file=sys.stderr)

    print(
        f"\nTotal: {total_messages} messages parsed from {len(txt_files)} files ({total_excluded} excluded)"
    )


if __name__ == "__main__":
    main()
