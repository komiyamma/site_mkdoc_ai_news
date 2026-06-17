@echo off
REM バッチファイルのあるディレクトリに移動
cd /d %~dp0

REM fix_frontmatter_dates.bat を実行し、終了を待つ
call fix_frontmatter_dates.bat

python convert_full_width_digits.py

REM 2秒待機
timeout /t 2 /nobreak >nul


python filter_md_files.py
if errorlevel 1 exit /b %ERRORLEVEL%

for /f "usebackq delims=" %%A in ("filtered_md_files.txt") do goto run_codex

echo No target markdown files. Skipping codex.
exit /b 0

:run_codex
call hermes -z "@gemini_command.mdの内容を実行して。画面には進捗以外の情報が出す必要はありません。要約に「一週間だった」とか「１日だった」などは記載しないこと。最後にこのリポジトリに対して、適切なコミットメッセージとともに全てコミット＆プッシュしてください。"

rem call codex --yolo -m "gpt-5.4-mini" exec "@gemini_command.mdの内容を実行して。画面には進捗以外の情報が出す必要はありません。要約に「一週間だった」とか「１日だった」などは記載しないこと。最後にこのリポジトリに対して、適切なコミットメッセージとともに全てコミット＆プッシュしてください。"

REM call agy -p "@gemini_command.mdの内容を実行して。画面には進捗以外の情報が出す必要はありません。最後にこのリポジトリに対して、適切なコミットメッセージとともに全てコミット＆プッシュしてください。"

REM qwen --yolo exec "@gemini_command.mdの内容を実行して。画面には進捗以外の情報が出す必要はありません。最後にこのリポジトリに対して、適切なコミットメッセージとともに全てコミット＆プッシュしてください。"


exit
