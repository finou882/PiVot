"""
Raspberry Pi Camera V1 Controller
RaspberryPi Camera V1での画像撮影制御
"""

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
import logging

# Raspberry Pi Camera用ライブラリ
try:
    from picamera import PiCamera
    from picamera.exc import PiCameraError
    PICAMERA_AVAILABLE = True
    print("✅ PiCamera library available")
except ImportError:
    PICAMERA_AVAILABLE = False
    print("⚠️ PiCamera library not available - using mock mode")

# PIL for image processing
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ PIL not available")

logger = logging.getLogger(__name__)

class PiCameraController:
    """Raspberry Pi Camera V1 制御クラス"""
    
    def __init__(self, 
                 resolution: Tuple[int, int] = (1920, 1080),
                 image_dir: str = "./captured_images",
                 mock_mode: bool = False):
        """
        Args:
            resolution: カメラ解像度 (width, height)
            image_dir: 撮影画像の保存ディレクトリ
            mock_mode: テスト用のモックモード
        """
        self.resolution = resolution
        self.image_dir = Path(image_dir)
        self.mock_mode = mock_mode or not PICAMERA_AVAILABLE
        self.camera = None
        
        # 保存ディレクトリを作成
        self.image_dir.mkdir(parents=True, exist_ok=True)
        
        # カメラ初期化
        self._initialize_camera()
    
    def _initialize_camera(self) -> bool:
        """カメラを初期化"""
        if self.mock_mode:
            print("📷 Mock mode - Camera simulation enabled")
            return True
            
        try:
            self.camera = PiCamera()
            self.camera.resolution = self.resolution
            self.camera.rotation = 0  # 必要に応じて調整
            
            # カメラのウォームアップ
            time.sleep(2)
            print(f"✅ PiCamera initialized - Resolution: {self.resolution}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Camera initialization failed: {e}")
            self.mock_mode = True
            print("⚠️ Falling back to mock mode")
            return False
    
    def capture_image(self, custom_filename: Optional[str] = None) -> Tuple[str, str]:
        """
        画像を撮影し、年月日時秒をIDとして保存
        
        Args:
            custom_filename: カスタムファイル名（拡張子なし）
            
        Returns:
            Tuple[image_path, image_id]: 画像パスとID
        """
        try:
            # 撮影時刻からIDを生成
            now = datetime.now()
            image_id = now.strftime("%Y%m%d%H%M%S")  # 年月日時分秒
            
            # ファイル名決定
            if custom_filename:
                filename = f"{custom_filename}_{image_id}.jpg"
            else:
                filename = f"capture_{image_id}.jpg"
                
            image_path = self.image_dir / filename
            
            if self.mock_mode:
                # モックモード: ダミー画像を作成
                self._create_mock_image(str(image_path))
                print(f"📷 Mock capture: {filename}")
            else:
                # 実際の撮影
                self.camera.capture(str(image_path))
                print(f"📷 Image captured: {filename}")
            
            return str(image_path), image_id
            
        except Exception as e:
            logger.error(f"❌ Image capture failed: {e}")
            raise Exception(f"Failed to capture image: {e}")
    
    def _create_mock_image(self, image_path: str):
        """テスト用のダミー画像を作成"""
        if not PIL_AVAILABLE:
            # PILがない場合は空ファイルを作成
            with open(image_path, 'wb') as f:
                f.write(b'mock_image_data')
            return
            
        # 簡単なダミー画像を作成
        from PIL import Image, ImageDraw, ImageFont
        
        # 画像作成
        img = Image.new('RGB', self.resolution, color=(100, 150, 200))
        draw = ImageDraw.Draw(img)
        
        # テキスト描画
        text = f"Mock Image\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        try:
            # システムフォントを使用
            font = ImageFont.load_default()
        except:
            font = None
            
        # 中央にテキスト配置
        x, y = self.resolution[0] // 2, self.resolution[1] // 2
        draw.text((x-100, y-20), text, fill=(255, 255, 255), font=font)
        
        # 保存
        img.save(image_path, 'JPEG', quality=85)
    
    def capture_with_preview(self, preview_time: int = 3) -> Tuple[str, str]:
        """
        プレビュー付きで撮影
        
        Args:
            preview_time: プレビュー表示時間（秒）
            
        Returns:
            Tuple[image_path, image_id]: 画像パスとID
        """
        if not self.mock_mode and self.camera:
            try:
                # プレビュー開始
                self.camera.start_preview()
                time.sleep(preview_time)
                
                # 撮影
                result = self.capture_image()
                
                # プレビュー停止
                self.camera.stop_preview()
                
                return result
                
            except Exception as e:
                logger.error(f"❌ Preview capture failed: {e}")
                # プレビュー失敗時は通常撮影
                return self.capture_image()
        else:
            # モックモードでは通常撮影
            return self.capture_image()
    
    def get_image_info(self, image_path: str) -> dict:
        """画像情報を取得"""
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found: {image_path}")
            
            # ファイル情報
            stat = os.stat(image_path)
            info = {
                "path": image_path,
                "size_bytes": stat.st_size,
                "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
            
            # 画像情報（PILが利用可能な場合）
            if PIL_AVAILABLE:
                try:
                    with Image.open(image_path) as img:
                        info.update({
                            "width": img.width,
                            "height": img.height,
                            "format": img.format,
                            "mode": img.mode
                        })
                except Exception as e:
                    logger.warning(f"Failed to get image info: {e}")
            
            return info
            
        except Exception as e:
            logger.error(f"❌ Failed to get image info: {e}")
            return {}
    
    def cleanup(self):
        """カメラリソースをクリーンアップ"""
        if self.camera and not self.mock_mode:
            try:
                self.camera.close()
                print("📷 Camera closed")
            except Exception as e:
                logger.error(f"❌ Camera cleanup failed: {e}")
    
    def __del__(self):
        """デストラクタ"""
        self.cleanup()

# デフォルトインスタンス
default_camera = PiCameraController()

# テスト関数
def test_camera():
    """カメラテスト"""
    print("📷 Testing Raspberry Pi Camera...")
    
    camera = PiCameraController(mock_mode=True)  # テスト用にモックモード
    
    try:
        # 撮影テスト
        image_path, image_id = camera.capture_image()
        print(f"✅ Test capture successful:")
        print(f"   Path: {image_path}")
        print(f"   ID: {image_id}")
        
        # 画像情報取得テスト
        info = camera.get_image_info(image_path)
        print(f"✅ Image info: {info}")
        
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
    finally:
        camera.cleanup()

if __name__ == "__main__":
    test_camera()