import os
# プレビューに関する環境変数を設定（GUI関連の問題を回避）
os.environ['LIBCAMERA_LOG_LEVELS'] = 'WARN'

try:
    from picamera2 import Picamera2
    import time
    
    print("カメラを初期化中...")
    
    # Picamera2オブジェクトを作成
    picam2 = Picamera2()
    
    # 静止画撮影用の設定を生成（より安全な解像度に変更）
    camera_config = picam2.create_still_configuration(
        main={"size": (1640, 1232)},  # V1カメラの標準解像度
        buffer_count=1
    )
    
    # カメラ設定を適用
    picam2.configure(camera_config)
    
    print("カメラを起動中...")
    # カメラを起動
    picam2.start()
    
    # センサーが安定するまで少し待つ
    print("カメラの準備完了まで待機中...")
    time.sleep(3)
    
    print("写真を撮影中...")
    # 画像をキャプチャしてファイルに保存
    picam2.capture_file("test_photo.jpg")
    
    # カメラを停止
    picam2.stop()
    
    print("画像を保存しました: test_photo.jpg")
    
except Exception as e:
    print(f"エラーが発生しました: {e}")
    print("カメラが接続されているか確認してください。")
    
    # カメラデバイスの確認
    if os.path.exists('/dev/video0'):
        print("カメラデバイス /dev/video0 が見つかりました")
    else:
        print("カメラデバイスが見つかりません")
