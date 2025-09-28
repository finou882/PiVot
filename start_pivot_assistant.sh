#!/bin/bash
# PiVot Smart Assistant Startup Script (Linux/Raspberry Pi)
# PiVot(Linux) ⟷ PiVot-Server(Windows) 構成用
# 使用方法: ./start_pivot_assistant.sh

echo "🤖 Starting PiVot Smart Voice Assistant System"
echo "Environment: PiVot(Linux) ⟷ PiVot-Server(Windows)"
echo "================================================"

# 0. ネットワーク設定確認
echo "🔍 Checking network configuration..."
python3 network_setup.py

read -p "📝 Continue with current configuration? (y/N): " -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Configuration cancelled. Please update config.py manually."
    exit 1
fi

# 1. Windows PC の PiVot-Server が起動しているか確認
echo "🧠 Checking PiVot-Server (Windows PC)..."
WINDOWS_IP=$(grep "WINDOWS_PC_IP" config.py | cut -d'"' -f2)
echo "   Windows PC IP: $WINDOWS_IP"

# ヘルスチェック
if curl -s --max-time 5 "http://$WINDOWS_IP:8001/health" > /dev/null; then
    echo "   ✅ PiVot-Server is running"
else
    echo "   ❌ PiVot-Server not accessible"
    echo "   💡 Make sure PiVot-Server is running on Windows PC"
    echo "   💡 Check IP address and firewall settings"
    read -p "🔄 Continue anyway? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 2. PiVot Assistant (メインシステム) を起動
echo "🎤 Starting PiVot Smart Assistant (Linux)..."
python3 main.py &
ASSISTANT_PID=$!
echo "   Assistant PID: $ASSISTANT_PID"

echo "================================================"
echo "✅ PiVot Smart Assistant System Started!"
echo ""
echo "🔗 Remote Services (Windows PC):"
echo "   NPU Server: http://$WINDOWS_IP:8001"
echo "   Upload Server: http://$WINDOWS_IP:8002"
echo "   Swagger UI: http://$WINDOWS_IP:8001/docs"
echo ""
echo "🎤 Say 'taro_tsuu' to activate the assistant"
echo "📷 Camera will capture and send to Windows PC for NPU processing"
echo "🛑 Press Ctrl+C to stop the assistant"
echo "================================================"

# Ctrl+C でクリーンアップ
cleanup() {
    echo ""
    echo "🛑 Stopping PiVot Smart Assistant..."
    kill $ASSISTANT_PID 2>/dev/null
    echo "✅ Assistant stopped"
    exit 0
}

trap cleanup INT

# メインプロセスを待機
wait $ASSISTANT_PID