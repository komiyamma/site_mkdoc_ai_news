@echo off
REM バッチファイルのあるディレクトリに移動
cd /d %~dp0

REM fix_frontmatter_dates.bat を実行し、終了を待つ
call fix_frontmatter_dates.bat

python convert_full_width_digits.py

REM 2秒待機
timeout /t 2 /nobreak >nul


call hermes -z "@gemini_command.mdの内容を実行して。画面には進捗以外の情報が出す必要はありません。要約に「一週間だった」とか「１日だった」などは記載しないこと。最後にこのリポジトリに対して、適切なコミットメッセージとともに全てコミット＆プッシュしてください。"

REM call codex --yolo -m "gpt-5.4-mini" exec "@gemini_command.mdの内容を実行して。画面には進捗以外の情報が出す必要はありません。要約に「一週間だった」とか「１日だった」などは記載しないこと。最後にこのリポジトリに対して、適切なコミットメッセージとともに全てコミット＆プッシュしてください。"

REM call gemini --yolo --prompt "@gemini_command.mdの内容を実行して。画面には進捗以外の情報が出す必要はありません。最後にこのリポジトリに対して、適切なコミットメッセージとともに全てコミット＆プッシュしてください。"

REM qwen --yolo exec "@gemini_command.mdの内容を実行して。画面には進捗以外の情報が出す必要はありません。最後にこのリポジトリに対して、適切なコミットメッセージとともに全てコミット＆プッシュしてください。"

exit
