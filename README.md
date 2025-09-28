# PiVot Smart Voice Assistant

🤖 **Raspberry Pi Camera V1 + Intel NPU統合音声アシスタント**

## 🌟 システム概要

PiVotの既存音声システムを拡張し、**Raspberry Pi Camera V1**で撮影した画像を**Intel NPU**で解析する完全統合音声アシスタントシステムです。

### �️ システム構成

```
🐧 Raspberry Pi (Linux)          🖥️ Windows PC
     PiVot Assistant    ⟷        PiVot-Server
┌─────────────────────┐         ┌─────────────────────┐
│ 🎤 Wake Word        │         │ 🧠 Intel NPU       │
│ 📷 Pi Camera V1     │  HTTP   │ ⚡ 6-15ms Inference │
│ 🔊 Voice Synthesis  │ ⟷      │ 📤 Image Upload     │
│ 🎯 taro_tsuu Model  │         │ 📊 Swagger UI       │
└─────────────────────┘         └─────────────────────┘
     Port: -                          Port: 8001, 8002
```

### �🎯 主要機能

- **🎤 ウェイクワード検出**: "taro_tsuu"で起動
- **📷 自動撮影**: Raspberry Pi Camera V1で高品質撮影  
- **🧠 NPU推論**: Intel NPUによる超高速画像解析（Windows PC）
- **🔊 音声合成**: VOICEVOX による自然な音声読み上げ
- **⚡ ネットワーク統合**: Linux ⟷ Windows クロスプラットフォーム

### 🔄 動作フロー

```
🐧 Raspberry Pi (Linux)                    🖥️ Windows PC
                                           
1. 🎤 ウェイクワード検出 ("taro_tsuu")
       ↓
2. 📷 Pi Camera V1で撮影
       ↓ (年月日時分秒ID)
3. 📤 HTTP送信 ──────────────→ 4. 📥 画像受信・保存
       ↓                                ↓
   🔄 待機中                        5. 🧠 Intel NPU解析
       ↓                                ↓ (6-15ms)
7. 🔊 音声読み上げ ←────────────── 6. 📤 解析結果返送
```

## 📁 システム構成

```
📦 PiVot/
├── 🎤 main.py                          # メイン統合システム
├── 🧪 test_system.py                   # システムテストスクリプト
├── 🚀 start_pivot_assistant.sh         # 起動スクリプト (Linux)
├── 🚀 start_pivot_assistant.bat        # 起動スクリプト (Windows)
└── 📁 s_compornents/
    ├── 📷 pi_camera_controller.py      # Raspberry Pi Camera制御
    ├── 🔗 pivot_server_client.py       # PiVot-Server連携クライアント
    ├── 📤 image_upload_server.py       # 画像アップロードサーバー
    ├── 🎤 wakeword_detect_ext.py       # ウェイクワード検出 (既存)
    ├── 🔊 voice.py                     # 音声合成 (既存)
    ├── 📋 requirements.txt             # 更新済み依存関係
    └── 📁 compornents/
        └── 🎯 taro_tsuu.onnx           # ウェイクワードモデル
```

## 🛠️ セットアップ

### � ワンコマンドセットアップ（推奨）

#### Raspberry Pi / Linux:
```bash
curl -sSL https://raw.githubusercontent.com/finou882/PiVot/main/setup_all.sh | bash
```

#### Windows PC:
```cmd
powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/finou882/PiVot/main/setup_all_windows.bat' -OutFile 'setup.bat'" && setup.bat
```

#### 手動セットアップ（必要な場合）:
```bash
# リポジトリをクローン
git clone https://github.com/finou882/PiVot.git
cd PiVot

# 完全セットアップ実行
python3 s_compornents/setup_1.py

# または依存関係のみ
pip3 install -r s_compornents/requirements.txt
```

⚠️ **セットアップで問題が発生した場合**: [../TROUBLESHOOTING.md](../TROUBLESHOOTING.md) を参照してください。

### �📋 前提条件

**🐧 Raspberry Pi (Linux側):**
- Raspberry Pi 4 以降推奨
- Raspberry Pi Camera V1 接続済み
- Python 3.8以上
- 同一ネットワーク接続

**🖥️ Windows PC:**
- Intel NPU搭載 (推奨)
- Python 3.8以上  
- PiVot-Server インストール済み
- 同一ネットワーク接続

### 1. Windows PC セットアップ

#### PiVot-Server 起動:
```cmd
cd C:\path\to\pivot-server
start_pivot_server.bat
```

このスクリプトは自動で：
- Windows IP アドレス表示
- ファイアウォール設定 (ポート 8001, 8002)
- PiVot-Server 起動
- ヘルスチェック実行

### 2. Raspberry Pi セットアップ

#### 依存関係インストール:
```bash
cd PiVot/s_compornents
pip3 install -r requirements.txt
```

#### カメラ有効化:
```bash
sudo raspi-config
# Interface Options → Camera → Enable
sudo reboot

# テスト撮影
raspistill -v -o test.jpg
```

#### ネットワーク設定:
```bash
cd PiVot
python3 network_setup.py
```

このスクリプトは自動で：
- Windows PC の IP アドレス検出
- PiVot-Server 接続確認
- config.py の自動更新

### 3. 手動設定 (必要な場合)

Windows PC の IP アドレスを手動で設定：

```bash
# Windows PC で IP 確認
ipconfig

# Raspberry Pi で config.py 編集
nano config.py
# WINDOWS_PC_IP = "192.168.1.XXX"  # 実際のIPに変更
```

## 🚀 システム起動

### 🔴 重要: 起動順序

1. **🖥️ Windows PC**: PiVot-Server を最初に起動
2. **🐧 Raspberry Pi**: PiVot Assistant を起動

### Windows PC (PiVot-Server) 起動

```cmd
cd C:\path\to\pivot-server
start_pivot_server.bat
```

画面に表示される Windows IP をメモしてください。

### Raspberry Pi (PiVot Assistant) 起動

#### 自動起動 (推奨):
```bash
cd PiVot
chmod +x start_pivot_assistant.sh
./start_pivot_assistant.sh
```

スクリプトが自動で：
- ネットワーク設定確認
- Windows PC 接続テスト
- PiVot Assistant 起動

#### 手動起動:
```bash
cd PiVot
python3 main.py
```

## 🎯 使用方法

1. **システム起動後**、マイクが"taro_tsuu"を待機します
2. **「タロー、ツー」と発話**してシステムを起動
3. **自動で撮影**が開始されます
4. **NPU解析**が実行され、結果が音声で読み上げられます

### 💡 使用例

```
👤 User: "タロー、ツー"
🤖 Assistant: "はい、何でしょうか？"
🤖 Assistant: "写真を撮影します"
📷 Camera: カシャ！
🤖 Assistant: "画像を解析しています"
🧠 NPU: 解析中...
🤖 Assistant: "写っているのは赤いリンゴです。新鮮そうで美味しそうですね。"
```

## ⚙️ 設定カスタマイズ

### main.py内の主要設定:

```python
# カメラ設定
self.camera = PiCameraController(
    resolution=(1920, 1080),        # 解像度
    image_dir="./captured_images",  # 保存ディレクトリ
    mock_mode=False                 # True=テストモード
)

# サーバー設定
self.pivot_client = PiVotServerClient(
    server_url="http://localhost:8001",      # NPU推論サーバー
    image_upload_server="http://localhost:8002"  # 画像アップロード
)

# ウェイクワード設定
cooldown=2.0  # 連続検出防止時間(秒)
threshold=0.01  # 検出閾値
```

## 🔧 テストとデバッグ

### システムテスト実行:
```bash
cd PiVot
python test_system.py
```

### 個別コンポーネントテスト:
```bash
# カメラテスト
python s_compornents/pi_camera_controller.py

# PiVot-Server接続テスト  
python s_compornents/pivot_server_client.py

# アップロードサーバーテスト
python s_compornents/image_upload_server.py
```

## 📊 システム情報

### 🌐 サービス一覧:

**🖥️ Windows PC (PiVot-Server):**
- **NPU推論サーバー**: `http://[Windows-IP]:8001`
- **画像アップロードサーバー**: `http://[Windows-IP]:8002`  
- **Swagger UI**: `http://[Windows-IP]:8001/docs`

**🐧 Raspberry Pi (PiVot Assistant):**
- **ローカル処理**: カメラ、音声、ウェイクワード検出

### ⚡ パフォーマンス:
- **撮影時間**: 1-2秒 (Pi Camera V1)
- **ネットワーク転送**: 0.5-2秒 (画像サイズ依存)
- **NPU推論**: 6-15ms (Windows PC)
- **音声合成**: 1-3秒 (Raspberry Pi)
- **総処理時間**: 8-15秒

### 🔧 ネットワーク要件:
- **帯域幅**: 最小1Mbps (画像転送用)
- **レイテンシ**: 100ms以下推奨
- **ポート**: 8001 (NPU), 8002 (Upload) 開放必須

## 🚨 トラブルシューティング

### 🌐 ネットワーク接続問題

1. **Windows PC が見つからない**
```bash
# Raspberry Pi で実行
python3 network_setup.py
ping [Windows-IP]
```

2. **ポート接続エラー**
```cmd
# Windows PC で確認
netstat -an | findstr :8001
netstat -an | findstr :8002

# ファイアウォール確認
netsh advfirewall firewall show rule name="PiVot-Server"
```

3. **IP アドレス変更時**
```bash
# config.py を手動更新
nano config.py
# WINDOWS_PC_IP = "新しいIP"
```

### 🔧 ハードウェア問題

1. **カメラエラー**
```bash
# カメラプロセス停止
sudo pkill -f "python.*camera"
# カメラ再有効化
sudo raspi-config
```

2. **音声出力エラー**
```bash
# 音声デバイス確認
python3 s_compornents/rr.py
# ALSA設定確認
aplay -l
```

3. **NPU接続エラー**
```bash
# PiVot-Server ヘルスチェック
curl http://[Windows-IP]:8001/health
curl http://[Windows-IP]:8002/health
```

### 📋 ログ確認

**Raspberry Pi:**
```bash
# メインログ
tail -f /var/log/syslog | grep python

# PiVot Assistant ログ
python3 main.py 2>&1 | tee pivot.log
```

**Windows PC:**
```cmd
# PiVot-Server コンソール出力を確認
# エラー詳細は起動ウィンドウに表示
```

### 🔄 システム再起動手順

1. **Raspberry Pi 停止**: Ctrl+C
2. **Windows PC 停止**: ウィンドウを閉じる
3. **Windows PC 起動**: `start_pivot_server.bat`
4. **Raspberry Pi 起動**: `./start_pivot_assistant.sh`

## 📈 拡張可能性

- **質問テキストのカスタマイズ**: `process_visual_query()`内でクエリを変更
- **複数カメラ対応**: カメラコントローラーの拡張
- **クラウド連携**: 画像をクラウドストレージにバックアップ
- **音声コマンド追加**: ウェイクワード後の音声認識統合

## 📜 ライセンス

このプロジェクトは既存のPiVotライセンスに準拠します。

---

**🎉 PiVot Smart Voice Assistant - Intel NPU × Raspberry Pi Camera統合システム完成！**