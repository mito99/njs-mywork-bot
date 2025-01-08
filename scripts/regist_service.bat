@echo off
setlocal

set "SCRIPT_DIR=%~dp0"

schtasks /create ^
    /tn "SlackBotService" ^
    /tr "\"%SCRIPT_DIR%start_service.bat\"" ^
    /sc onstart ^
    /ru System ^
    /f ^
    /delay 0001:00

if %ERRORLEVEL% equ 0 (
    echo タスクが正常に登録されました。
    echo タスクを開始します...
    schtasks /run /tn "SlackBotService"
) else (
    echo タスクの登録に失敗しました。
)

endlocal
pause