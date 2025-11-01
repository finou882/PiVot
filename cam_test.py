import time
import argparse
from picamera2 import Picamera2

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cam_test.py
Raspberry Pi 4 + OV5647 (camera module) で写真を撮る簡単なスクリプト(Picamera2 使用）
使い方:
    python3 cam_test.py -o photo.jpg -w 2592 -t 1944 -d 2
備考:
    - CUI環境向けにプレビュー機能を無効化済み
"""


def main():
    p = argparse.ArgumentParser(description="Take a still image with OV5647 using Picamera2")
    p.add_argument("-o", "--output", default="photo.jpg", help="output filename (jpg)")
    p.add_argument("-w", "--width", type=int, default=2592, help="image width (pixels)")
    p.add_argument("-t", "--height", type=int, default=1944, help="image height (pixels)")
    p.add_argument("-d", "--delay", type=float, default=2.0, help="warm-up delay in seconds")
    args = p.parse_args()

    picam2 = Picamera2()
    
    # CUI環境最適化: display="main" を追加し、プレビュー依存のエラーを回避
    # スティル撮影用設定。
    config = picam2.create_still_configuration(
        main={"size": (args.width, args.height)},
        display="main" 
    )
    picam2.configure(config)
    
    try:
        picam2.start(show_preview=False)
        # カメラの自動露出等が落ち着くまで少し待つ
        time.sleep(args.delay)
        picam2.capture_file(args.output)
        print("Saved:", args.output)
    finally:
        picam2.stop(show_preview)

# インデントエラー修正済み: 左端に揃える
if __name__ == "__main__":
    main()