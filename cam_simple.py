#!/usr/bin/env python3
"""
Simple camera capture using OpenCV or raspistill fallback
"""

import subprocess
import os
import time

def capture_with_raspistill():
    """raspistillコマンドを使って写真を撮影"""
    try:
        print("raspistillを使用して撮影中...")
        cmd = [
            "raspistill",
            "-o", "test_photo.jpg",
            "-w", "1920",
            "-h", "1080",
            "-t", "1000"  # 1秒のプレビュー
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("画像を保存しました: test_photo.jpg")
            return True
        else:
            print(f"raspistillエラー: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("raspistillコマンドが見つかりません")
        return False
    except Exception as e:
        print(f"raspistillでエラーが発生: {e}")
        return False

def capture_with_libcamera():
    """libcamera-stillコマンドを使って写真を撮影"""
    try:
        print("libcamera-stillを使用して撮影中...")
        cmd = [
            "libcamera-still",
            "-o", "test_photo.jpg",
            "--width", "1920",
            "--height", "1080",
            "--timeout", "1000"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("画像を保存しました: test_photo.jpg")
            return True
        else:
            print(f"libcamera-stillエラー: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("libcamera-stillコマンドが見つかりません")
        return False
    except Exception as e:
        print(f"libcamera-stillでエラーが発生: {e}")
        return False

def capture_with_opencv():
    """OpenCVを使って写真を撮影"""
    try:
        import cv2
        print("OpenCVを使用して撮影中...")
        
        # カメラを開く
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("カメラを開けませんでした")
            return False
        
        # 解像度を設定
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        
        # カメラが安定するまで待つ
        time.sleep(2)
        
        # フレームを読み取り
        ret, frame = cap.read()
        
        if ret:
            # 画像を保存
            cv2.imwrite("test_photo.jpg", frame)
            print("画像を保存しました: test_photo.jpg")
            success = True
        else:
            print("フレームの読み取りに失敗しました")
            success = False
        
        # カメラを解放
        cap.release()
        return success
        
    except ImportError:
        print("OpenCVがインストールされていません")
        return False
    except Exception as e:
        print(f"OpenCVでエラーが発生: {e}")
        return False

def main():
    print("カメラで写真を撮影します...")
    
    # まずlibcamera-stillを試す（Raspberry Pi OS Bullseye以降で推奨）
    if capture_with_libcamera():
        return
    
    # 次にraspistillを試す（古いRaspberry Pi OS）
    if capture_with_raspistill():
        return
    
    # 最後にOpenCVを試す
    if capture_with_opencv():
        return
    
    print("すべての方法で撮影に失敗しました。")
    print("カメラが正しく接続され、有効になっているか確認してください。")
    
    # カメラの状態を確認
    if os.path.exists('/dev/video0'):
        print("カメラデバイス /dev/video0 が見つかりました")
    else:
        print("カメラデバイスが見つかりません")

if __name__ == "__main__":
    main()