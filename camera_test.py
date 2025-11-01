from picamera2 import Picamera2
import time

# Picamera2オブジェクトを作成
picam2 = Picamera2()

# プレビュー用の設定を作成
# OV5647は最大 2592x1944 (5MP)
camera_config = picam2.create_still_configuration(main={"size": (1280, 720)}) 
picam2.configure(camera_config)

# カメラを開始
picam2.start()

# センサーが安定するのを待つ (プレビューがない場合は特に重要)
time.sleep(2)

# 写真を撮影してファイルに保存
# ファイル名は適宜変更してください
file_path = "/home/pi/test_photo.jpg" 
picam2.capture_file(file_path)

# カメラを停止
picam2.stop()

print(f"写真が {file_path} に保存されました。")
