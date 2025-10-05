@echo off
REM PiVot Smart Assistant - Windows One Command Setup
REM ワンコマンド完全セットアップスクリプト（Windows版）
REM 使用方法: setup_all_windows.bat

echo 🚀 PiVot Smart Assistant - Windows Setup
echo ===========================================

REM 1. システム情報表示
echo 🔍 System Information:
echo    OS: %OS%
echo    User: %USERNAME%
python --version 2>nul && echo    Python: Found || echo    Python: Not found

REM 2. Python チェック
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is required but not installed
    echo 💡 Please install Python from https://python.org
    echo 💡 Make sure to check "Add Python to PATH"
    pause
    exit /b 1
) else (
    echo ✅ Python found
)

REM 3. pip チェック
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip is required but not found
    echo 💡 Please reinstall Python with pip
    pause
    exit /b 1
) else (
    echo ✅ pip found
)

REM 4. git チェック
git --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️ git not found
    echo 💡 Please install Git from https://git-scm.com/
    echo 💡 Or download PiVot manually from GitHub
    set SKIP_GIT=1
) else (
    echo ✅ git found
    set SKIP_GIT=0
)

REM 5. PiVot リポジトリの取得
echo.
echo 📥 Getting PiVot repository...
set "PIVOT_DIR=%USERPROFILE%\PiVot"

if "%SKIP_GIT%"=="1" (
    echo    Please download PiVot manually to: %PIVOT_DIR%
    echo    From: https://github.com/finou882/PiVot
    pause
) else (
    if exist "%PIVOT_DIR%" (
        echo    Directory exists, updating...
        cd /d "%PIVOT_DIR%"
        git pull origin main
    ) else (
        echo    Cloning repository...
        git clone https://github.com/finou882/PiVot.git "%PIVOT_DIR%"
        cd /d "%PIVOT_DIR%"
    )
)

REM 6. セットアップスクリプト実行
echo.
echo 🔧 Running complete setup...
cd s_compornents
python setup_1.py

if errorlevel 1 (
    echo ❌ Setup script failed
    pause
    exit /b 1
)

REM 7. 設定確認
echo.
echo ⚙️ Configuration check...
python -c "import sys; print('🐍 Python executable:', sys.executable)" 2>nul || echo ⚠️ Python check failed
python -c "import requests; print('🌐 HTTP client: OK')" 2>nul || echo ⚠️ HTTP client needs attention
python -c "import aiohttp; print('🔗 Async HTTP: OK')" 2>nul || echo ⚠️ Async HTTP needs attention

REM 8. 完了メッセージ
echo.
echo ===========================================
echo 🎉 PiVot Windows Setup Complete!
echo.
echo 📂 Installation Directory: %PIVOT_DIR%
echo.
echo 🔧 This Windows PC is ready to run PiVot-Server
echo.
echo ▶️ To start PiVot-Server:
echo    1. Open Command Prompt as Administrator
echo    2. cd %PIVOT_DIR%\..\pivot-server
echo    3. start_pivot_server.bat
echo.
echo 🐧 Raspberry Pi Setup:
echo    Run this command on Raspberry Pi:
echo    curl -sSL https://raw.githubusercontent.com/finou882/PiVot/main/setup_all.sh ^| bash
echo.
echo 📚 Documentation:
echo    README.md in %PIVOT_DIR%
echo.
echo ===========================================
pause