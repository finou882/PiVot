# PiVot Smart Assistant - Command Reference
# 全コマンド一覧とクイックリファレンス

# ============================================
# 🚀 ワンコマンドセットアップ
# ============================================

# 【Raspberry Pi / Linux】超簡単セットアップ
curl -sSL https://raw.githubusercontent.com/finou882/PiVot/main/setup_all.sh | bash

# 【Windows】超簡単セットアップ
# PowerShell で実行:
# Invoke-WebRequest -Uri "https://raw.githubusercontent.com/finou882/PiVot/main/setup_all_windows.bat" -OutFile "setup.bat" && .\setup.bat

# ============================================
# 📦 手動インストールコマンド
# ============================================

# 【基本セットアップ】
cd PiVot/s_compornents
python3 setup_1.py

# 【依存関係のみインストール】
pip3 install -r s_compornents/requirements.txt

# 【クイックインストール】
python3 quick_install.py

# ============================================
# 🔧 個別インストールコマンド
# ============================================

# 【Python基本パッケージ】
pip3 install openwakeword aiohttp fastapi uvicorn pillow requests asyncio

# 【Raspberry Pi追加パッケージ】
sudo apt install python3-pyaudio portaudio19-dev python3-picamera espeak
pip3 install pyaudio

# 【Windows NPU関連パッケージ】
pip install openvino transformers numpy torch

# ============================================
# ⚙️ システム設定コマンド
# ============================================

# 【Raspberry Pi Camera有効化】
sudo raspi-config
# → Interface Options → Camera → Enable

# 【オーディオ設定確認】
python3 s_compornents/rr.py

# 【カメラテスト】
raspistill -v -o test.jpg

# 【権限設定】
sudo usermod -a -G audio $USER
sudo usermod -a -G video $USER

# ============================================
# 🌐 ネットワーク設定コマンド
# ============================================

# 【Windows PC自動検出】
python3 network_setup.py

# 【手動IP設定】
nano config.py  # WINDOWS_PC_IP を編集

# 【接続テスト】
python3 test_cross_platform.py

# ============================================
# 🚀 起動コマンド
# ============================================

# 【PiVot-Server起動 (Windows PC)】
python main_npu.py
# または
start_pivot_server.bat

# 【PiVot Assistant起動 (Raspberry Pi)】
./start_pivot_assistant.sh
# または
python3 main.py

# ============================================
# 🧪 テストコマンド
# ============================================

# 【システム全体テスト】
python3 test_system.py

# 【クロスプラットフォームテスト】
python3 test_cross_platform.py

# 【個別コンポーネントテスト】
python3 s_compornents/pi_camera_controller.py      # カメラテスト
python3 s_compornents/pivot_server_client.py       # サーバー接続テスト
python3 s_compornents/image_upload_server.py       # アップロードサーバーテスト

# ============================================
# 🛠️ メンテナンスコマンド
# ============================================

# 【ログ確認】
tail -f /var/log/syslog | grep python

# 【プロセス確認】
ps aux | grep python
ps aux | grep pivot

# 【ポート確認】
netstat -tuln | grep :8001
netstat -tuln | grep :8002

# 【システム情報】
python3 config.py  # 設定情報表示

# ============================================
# 🔄 アップデート・再インストール
# ============================================

# 【リポジトリ更新】
git pull origin main

# 【依存関係再インストール】
pip3 install --upgrade -r s_compornents/requirements.txt

# 【完全リセット】
rm -rf captured_images/ uploaded_images/ logs/
python3 s_compornents/setup_1.py

# ============================================
# 📚 ドキュメント・ヘルプ
# ============================================

# 【設定確認】
python3 -c "from config import print_config; print_config()"

# 【使用方法表示】
python3 main.py --help

# 【README表示】
cat README.md

# ============================================
# 🚨 トラブルシューティング
# ============================================

# 【権限エラー解決】
sudo chown -R $USER:$USER ~/PiVot
chmod +x start_pivot_assistant.sh

# 【ポート競合解決】
sudo lsof -i :8001
sudo lsof -i :8002
sudo kill -9 <PID>

# 【カメラエラー解決】
sudo pkill -f python.*camera
sudo modprobe bcm2835-v4l2

# 【音声エラー解決】
sudo systemctl restart pulseaudio
pulseaudio --kill && pulseaudio --start

# ============================================
# 💡 クイックスタートガイド
# ============================================

# 1. 【最初に一度だけ実行】
curl -sSL https://raw.githubusercontent.com/finou882/PiVot/main/setup_all.sh | bash

# 2. 【Windows PC設定】
python3 network_setup.py

# 3. 【システム起動】
./start_pivot_assistant.sh

# 4. 【使用開始】
# "タロー、ツー" と発話してアシスタント起動

# ============================================