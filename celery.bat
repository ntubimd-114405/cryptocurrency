@echo off
chcp 65001

:: 檢查是否以管理員身份執行
NET SESSION >nul 2>&1
if %errorlevel% NEQ 0 (
    echo 需要管理員權限來運行此批次文件。
    echo 正在以管理員身份重新啟動...
    powershell -Command "Start-Process cmd -ArgumentList '/c %~s0' -Verb runAs"
    exit /b
)

:: 切換到專案目錄
cd /d "c:\python project\cryptocurrency-ntub"

REM 進入虛擬環境
call ".venv\Scripts\activate.bat"

REM 啟動 Django 開發伺服器
start cmd /K "python manage.py runserver"

REM 啟動 MariaDB 服務
net start mariadb

REM 啟動 RabbitMQ 服務
net start RabbitMQ

REM 啟動 Celery worker
start cmd /K "celery -A cryptocurrency worker --loglevel=info --pool=solo"

REM 啟動 Celery beat
start cmd /K "celery -A cryptocurrency beat --loglevel=info"
