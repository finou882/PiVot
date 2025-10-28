#!/usr/bin/env python3
"""
カメラ機能のテスト用スクリプト
Windows環境でのモック機能をテスト
"""

import os
import platform
import time
from PIL import Image, ImageDraw

# プラットフォーム検出
IS_WINDOWS = platform.system() == "Windows"
IS_RASPBERRY_PI = os.path.exists('/opt/vc/bin/vcgencmd')

print(f"🖥️  Platform: {platform.system()}")
print(f"🔧 IS_WINDOWS: {IS_WINDOWS}")
print(f"🍓 IS_RASPBERRY_PI: {IS_RASPBERRY_PI}")

def test_mock_camera():
    """模擬カメラ機能をテスト"""
    path = "test_camera_image.jpg"
    
    if IS_WINDOWS:
        print("🖥️  Windows環境: 模擬カメラ画像を生成中...")
        try:
            # 640x480のテスト画像を生成
            test_image = Image.new('RGB', (640, 480), color=(73, 109, 137))
            # 簡単なテキストを追加
            draw = ImageDraw.Draw(test_image)
            draw.text((10, 10), f"Test Image - {time.strftime('%Y-%m-%d %H:%M:%S')}", fill=(255, 255, 255))
            draw.text((10, 50), f"Platform: {platform.system()}", fill=(255, 255, 255))
            draw.text((10, 90), "Mock Camera Test", fill=(255, 255, 255))
            
            test_image.save(path)
            print(f"📸 模擬画像を生成し、{path}に保存しました。")
            
            # 画像情報を表示
            if os.path.exists(path):
                img_size = os.path.getsize(path)
                print(f"📄 ファイルサイズ: {img_size} bytes")
                
                with Image.open(path) as img:
                    print(f"🖼️  画像サイズ: {img.size}")
                    print(f"🎨 画像モード: {img.mode}")
            
            return True
        except Exception as e:
            print(f"❌ 模擬画像の生成中にエラーが発生しました: {e}")
            return False
    else:
        print("ℹ️  非Windows環境では実際のカメラを使用します")
        return True

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 カメラ機能テスト開始")
    print("=" * 50)
    
    result = test_mock_camera()
    
    print("=" * 50)
    if result:
        print("✅ テスト成功!")
    else:
        print("❌ テスト失敗!")
    print("=" * 50)