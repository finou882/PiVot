@echo off
REM PiVot Smart Assistant Startup Script (Windows)
REM 使用方法: start_pivot_assistant.bat

echo 🤖 Starting PiVot Smart Voice Assistant System
echo ================================================

REM 1. PiVot-Server (NPU推論サーバー) を起動
echo 🧠 Starting PiVot-Server (NPU Inference)...
cd ..\..
start "PiVot-Server" python main_npu.py
echo    PiVot-Server started in new window

REM サーバー起動待機
timeout /t 5 /nobreak >nul

REM 2. PiVot Assistant (メインシステム) を起動
echo 🎤 Starting PiVot Smart Assistant...
cd PiVot
python main.py

echo ================================================
echo ✅ PiVot Smart Assistant System Started!
echo.
echo 🔗 Services:
echo    NPU Server: http://localhost:8001
echo    Upload Server: http://localhost:8002
echo    Swagger UI: http://localhost:8001/docs
echo.
echo 🎤 Say 'taro_tsuu' to activate the assistant
echo 🛑 Press Ctrl+C to stop the assistant
echo ================================================

pause