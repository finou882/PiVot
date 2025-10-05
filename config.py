# PiVot Smart Assistant Configuration
# 環境別設定ファイル

# ===========================================
# Network Configuration (ネットワーク設定)
# ===========================================

# Windows PC (PiVot-Server) の IP アドレス
# 実際の Windows PC の IP アドレスに変更してください
WINDOWS_PC_IP = "192.168.68.50"  # Updated from network detection

# PiVot-Server (Windows) 設定
PIVOT_SERVER_URL = f"http://{WINDOWS_PC_IP}:8000"
IMAGE_UPLOAD_SERVER_URL = f"http://{WINDOWS_PC_IP}:8001"

# ===========================================
# Raspberry Pi (PiVot) 設定
# ===========================================

# Raspberry Pi Camera 設定
CAMERA_RESOLUTION = (1920, 1080)  # カメラ解像度
CAMERA_MOCK_MODE = False  # True = テストモード, False = 実際のカメラ使用

# ウェイクワード設定
WAKEWORD_MODEL_PATH = "s_compornents/compornents/taro_tsuu.onnx"
WAKEWORD_THRESHOLD = 0.01  # 検出感度 (低いほど敏感)
WAKEWORD_COOLDOWN = 2.0  # 連続検出防止時間(秒)

# 音声設定
AUDIO_INPUT_DEVICE_INDEX = 2  # マイクデバイス番号 (rr.py で確認)
VOICEVOX_SPEAKER_ID = 11  # VOICEVOX話者ID

# ===========================================
# システム設定
# ===========================================

# タイムアウト設定
HTTP_TIMEOUT = 30  # HTTP通信タイムアウト(秒)
NPU_INFERENCE_TIMEOUT = 60  # NPU推論タイムアウト(秒)

# ディレクトリ設定
CAPTURED_IMAGES_DIR = "./captured_images"  # 撮影画像保存ディレクトリ

# デバッグ設定
DEBUG_MODE = True  # デバッグ情報表示
VERBOSE_LOGGING = True  # 詳細ログ出力

# ===========================================
# IP アドレス自動検出用設定
# ===========================================

# Windows PC を自動検出する場合の設定
AUTO_DETECT_WINDOWS_PC = False  # True = 自動検出, False = 手動設定
NETWORK_SCAN_RANGE = "192.168.1.0/24"  # スキャン範囲

# ===========================================
# 設定確認用の表示関数
# ===========================================

def print_config():
    """設定情報を表示"""
    print("🔧 PiVot Configuration")
    print("=" * 40)
    print(f"Windows PC IP: {WINDOWS_PC_IP}")
    print(f"PiVot-Server: {PIVOT_SERVER_URL}")
    print(f"Upload Server: {IMAGE_UPLOAD_SERVER_URL}")
    print(f"Camera Resolution: {CAMERA_RESOLUTION}")
    print(f"Camera Mock Mode: {CAMERA_MOCK_MODE}")
    print(f"Wakeword Threshold: {WAKEWORD_THRESHOLD}")
    print(f"Audio Device Index: {AUDIO_INPUT_DEVICE_INDEX}")
    print(f"Debug Mode: {DEBUG_MODE}")
    print("=" * 40)

if __name__ == "__main__":
    print_config()