#!/bin/bash
# PiVot Smart Assistant - One Command Setup
# ワンコマンド完全セットアップスクリプト
# 使用方法: curl -sSL https://raw.githubusercontent.com/finou882/PiVot/main/setup_all.sh | bash

echo "🚀 PiVot Smart Assistant - One Command Setup"
echo "=============================================="

# 1. システム情報表示
echo "🔍 System Information:"
echo "   OS: $(uname -s) $(uname -r)"
echo "   Architecture: $(uname -m)"
echo "   User: $USER"
echo "   Python: $(python3 --version 2>/dev/null || echo 'Not found')"

# 2. 前提条件チェック
echo ""
echo "🔧 Checking prerequisites..."

# Python 3 チェック
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    echo "💡 Install Python 3: sudo apt install python3 python3-pip"
    exit 1
else
    echo "✅ Python 3 found"
fi

# pip チェック
if ! command -v pip3 &> /dev/null; then
    echo "⚠️ pip3 not found, installing..."
    sudo apt update
    sudo apt install -y python3-pip
else
    echo "✅ pip3 found"
fi

# git チェック
if ! command -v git &> /dev/null; then
    echo "⚠️ git not found, installing..."
    sudo apt install -y git
else
    echo "✅ git found"
fi

# 3. システム依存関係の事前インストール
echo ""
echo "🔧 Installing system dependencies first..."

# PyAudio用の依存関係
echo "   Installing PortAudio (for PyAudio)..."
sudo apt update
sudo apt install -y portaudio19-dev python3-pyaudio

# PiCamera用の依存関係
echo "   Setting up Raspberry Pi camera..."
sudo apt install -y python3-picamera libraspberrypi-dev libraspberrypi-bin

# その他の音声・システム依存関係
echo "   Installing additional dependencies..."
sudo apt install -y python3-dev libasound2-dev pulseaudio alsa-utils
sudo apt install -y build-essential cmake pkg-config net-tools

# 4. PiVot リポジトリのクローン
echo ""
echo "📥 Cloning PiVot repository..."
PIVOT_DIR="$HOME/PiVot"

if [ -d "$PIVOT_DIR" ]; then
    echo "   Directory exists, updating..."
    cd "$PIVOT_DIR"
    git pull origin main
else
    echo "   Cloning repository..."
    git clone https://github.com/finou882/PiVot.git "$PIVOT_DIR"
    cd "$PIVOT_DIR"
fi

# 5. Python パッケージの個別インストール（エラー回避）
echo ""
echo "🐍 Installing Python packages (with error handling)..."
cd "$PIVOT_DIR/PiVot/s_compornents"

# PyAudioを先にシステムパッケージから試す
echo "   Installing PyAudio (system package)..."
sudo apt install -y python3-pyaudio || echo "   ⚠️ System PyAudio failed, will try pip later"

# PiCameraを先にシステムパッケージから試す
echo "   Installing PiCamera (system package)..."
sudo apt install -y python3-picamera || echo "   ⚠️ System PiCamera failed, will try pip later"

# その他のパッケージを先にインストール
echo "   Installing core packages..."
pip3 install --user openwakeword aiohttp fastapi uvicorn pillow requests asyncio

# エラーが出やすいパッケージを個別に試す
echo "   Installing audio packages (fallback)..."
pip3 install --user sounddevice || echo "   ⚠️ sounddevice failed"

# vosk と jaconv を個別に
echo "   Installing speech recognition..."
pip3 install --user vosk jaconv fugashi || echo "   ⚠️ Some speech packages failed"

# 最後に requirements.txt の残りを試す
echo "   Installing remaining packages..."
pip3 install --user -r requirements.txt || echo "   ⚠️ Some packages failed, but continuing..."

# 6. セットアップスクリプト実行
echo ""
echo "🔧 Running additional setup..."
python3 setup_1.py || echo "⚠️ Some setup steps failed, but installation may still work"

# 7. 実行権限設定
echo ""
echo "📝 Setting up permissions..."
chmod +x ../start_pivot_assistant.sh
chmod +x ../network_setup.py
chmod +x ../test_cross_platform.py

# 8. 設定確認
echo ""
echo "🔍 Verifying configuration..."

# Windows PC の IP を確認して設定
echo "Configuring Windows PC connection..."
python3 ../network_setup.py

# セットアップ完了
echo ""
echo "=============================================="
echo "🎉 PiVot Smart Assistant Setup Complete!"
echo ""
echo "📂 Installation Directory: $PIVOT_DIR"
echo ""
echo "🧪 To test your installation:"
echo "   cd $PIVOT_DIR/PiVot && python3 test_installation.py"
echo ""
echo "🔧 Next Steps:"
echo "   1. Configure Windows PC IP (if needed):"
echo "      cd $PIVOT_DIR && python3 network_setup.py"
echo ""
echo "   2. Enable Pi Camera (if using real camera):"
echo "      sudo raspi-config → Interface Options → Camera → Enable"
echo "      sudo reboot"
echo ""
echo "   3. Start PiVot Assistant:"
echo "      cd $PIVOT_DIR && ./start_pivot_assistant.sh"
echo ""
echo "   4. Test cross-platform connection:"
echo "      cd $PIVOT_DIR && python3 test_cross_platform.py"
echo ""
echo "🔗 Windows PC Setup:"
echo "   Make sure PiVot-Server is running on Windows PC"
echo "   Port 8000 should be accessible"
echo ""
echo "📚 Documentation & Troubleshooting:"
echo "   README.md and TROUBLESHOOTING.md in $PIVOT_DIR"
echo ""
echo "=============================================="