@echo off
setlocal

rem 絶対�スを使用して環境を設定
set "SCRIPT_DIR=%~dp0"
set "APP_DIR=%SCRIPT_DIR%.."
set "PYTHON_PATH=%APP_DIR%\.venv\Scripts\python.exe"
set "MAIN_SCRIPT=%APP_DIR%\src\main.py"

rem カレントディレクトリを設定
cd /d "%APP_DIR%"

rem 絶対パスで実行
"%PYTHON_PATH%" "%MAIN_SCRIPT%"

endlocal
