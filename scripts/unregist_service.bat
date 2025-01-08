@echo off
schtasks /delete ^
    /tn "SlackBotService" ^
    /f
if %ERRORLEVEL% equ 0 (
    echo Task deleted successfully.
) else (
    echo Failed to delete task.
)
pause