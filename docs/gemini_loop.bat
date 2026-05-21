for /L %%i in (1,1,2) do (
  echo [%%i/2] gemini 実行中...
  agy -p "gemini_command.mdの内容を実行してください。"
  echo [%%i/2] 終了コード=%errorlevel%
)