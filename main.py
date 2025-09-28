"""
PiVot Smart Voice Assistant with Intel NPU Vision
Raspberry Pi Camera V1 + PiVot-Server統合音声アシスタント

ワークフロー:
1. ウェイクワード検出 (taro_tsuu)
2. Raspberry Pi Camera V1で撮影
3. PiVot-Serverに画像送信 & NPU推論
4. 音声合成で結果を読み上げ

統合システム by PiVot + PiVot-Server
実行環境: PiVot(Linux) ⟷ PiVot-Server(Windows)
"""

import subprocess
import os
import asyncio
import threading
import time
from datetime import datetime
from typing import Optional

# 設定ファイルをインポート
from config import (
    PIVOT_SERVER_URL, IMAGE_UPLOAD_SERVER_URL,
    CAMERA_RESOLUTION, CAMERA_MOCK_MODE,
    WAKEWORD_MODEL_PATH, WAKEWORD_THRESHOLD, WAKEWORD_COOLDOWN,
    AUDIO_INPUT_DEVICE_INDEX, VOICEVOX_SPEAKER_ID,
    HTTP_TIMEOUT, CAPTURED_IMAGES_DIR,
    DEBUG_MODE, print_config
)

# 既存コンポーネント
from s_compornents.wakeword_detect_ext import WakewordDetector
from s_compornents.voice import speak

# 新しいコンポーネント
from s_compornents.pi_camera_controller import PiCameraController
from s_compornents.pivot_server_client import PiVotServerClient
from s_compornents.image_upload_server import ImageUploadServer

class PiVotSmartAssistant:
    """PiVot スマート音声アシスタント"""
    
    def __init__(self):
        print("🤖 PiVot Smart Voice Assistant Initializing...")
        print("=" * 60)
        
        # 設定情報を表示
        if DEBUG_MODE:
            print_config()
        
        # コンポーネント初期化
        self.camera = PiCameraController(
            resolution=CAMERA_RESOLUTION,
            image_dir=CAPTURED_IMAGES_DIR,
            mock_mode=CAMERA_MOCK_MODE
        )
        
        self.pivot_client = PiVotServerClient(
            server_url=PIVOT_SERVER_URL,
            timeout=HTTP_TIMEOUT,
            image_upload_server=IMAGE_UPLOAD_SERVER_URL
        )
        
        self.wakeword_detector = WakewordDetector(
            model_path=WAKEWORD_MODEL_PATH,
            inference_framework="onnx",
            chunk_size=1280,
            threshold=WAKEWORD_THRESHOLD,
            input_device_index=AUDIO_INPUT_DEVICE_INDEX,
            cooldown=WAKEWORD_COOLDOWN
        )
        
        # アップロードサーバー
        self.upload_server = None
        self.upload_server_thread = None
        
        # 状態管理
        self.is_processing = False
        self.last_processing_time = 0
        
        print("✅ PiVot Smart Assistant Ready!")
        print("Components:")
        print(f"  📷 Camera: {'Mock Mode' if self.camera.mock_mode else 'Pi Camera V1'}")
        print(f"  🧠 NPU Server: {self.pivot_client.server_url}")
        print(f"  📤 Upload Server: {self.pivot_client.image_upload_server}")
        print("=" * 60)
    
    def start_upload_server(self):
        """アップロードサーバーを別スレッドで起動"""
        def run_server():
            self.upload_server = ImageUploadServer()
            self.upload_server.start_server(host="0.0.0.0", port=8002, reload=False)
        
        self.upload_server_thread = threading.Thread(target=run_server, daemon=True)
        self.upload_server_thread.start()
        
        # サーバー起動待機
        time.sleep(3)
        print("📤 Image Upload Server started on port 8002")
    
    def start_voicevox_engine(self):
        """VOICEVOXエンジンを起動"""
        try:
            # Linux用のrun.shを実行
            run_sh_path = os.path.abspath("s_compornents/voicevox/linux-cpu/run.sh")
            if os.path.exists(run_sh_path):
                subprocess.run(["chmod", "+x", run_sh_path])
                subprocess.Popen([run_sh_path])
                print("🔊 VOICEVOX Engine started")
            else:
                print("⚠️ VOICEVOX run.sh not found - using system TTS")
        except Exception as e:
            print(f"⚠️ VOICEVOX startup failed: {e}")
    
    async def process_visual_query(self) -> bool:
        """視覚的質問処理パイプライン"""
        if self.is_processing:
            print("⏳ Already processing, skipping...")
            return False
        
        self.is_processing = True
        self.last_processing_time = time.time()
        
        try:
            print("\n🤖 Starting Visual AI Pipeline...")
            print("-" * 40)
            
            # ステップ1: 撮影
            print("📷 Step 1: Capturing image...")
            speak("写真を撮影します")
            
            image_path, image_id = self.camera.capture_image("assistant")
            print(f"   ✅ Image captured: {image_id}")
            
            # ステップ2: 画像情報表示
            image_info = self.camera.get_image_info(image_path)
            if image_info:
                print(f"   📊 Image: {image_info.get('width', 'Unknown')}x{image_info.get('height', 'Unknown')}, "
                      f"{image_info.get('size_bytes', 0) / 1024:.1f}KB")
            
            # ステップ3: NPU推論実行
            print("🧠 Step 2: NPU inference...")
            speak("画像を解析しています")
            
            success, response_text = await self.pivot_client.full_pipeline(
                image_path=image_path,
                image_id=image_id,
                query="この画像に何が写っていますか？詳しく説明してください。"
            )
            
            # ステップ4: 結果の音声読み上げ
            print("🔊 Step 3: Voice synthesis...")
            if success and response_text:
                print(f"   🧠 NPU Response: {response_text}")
                
                # 音声合成用に最適化
                optimized_text = self._optimize_for_speech(response_text)
                print(f"   🔊 Speech: {optimized_text}")
                
                speak(optimized_text)
                print("✅ Pipeline completed successfully!")
            else:
                error_message = "画像の解析に失敗しました。もう一度お試しください。"
                print(f"   ❌ NPU Error: {response_text}")
                speak(error_message)
                print("❌ Pipeline failed")
            
            print("-" * 40)
            return success
            
        except Exception as e:
            error_message = f"処理中にエラーが発生しました: {e}"
            print(f"❌ Pipeline error: {e}")
            speak("処理中にエラーが発生しました")
            return False
            
        finally:
            self.is_processing = False
    
    def _optimize_for_speech(self, text: str) -> str:
        """音声合成用にテキストを最適化"""
        if not text:
            return "解析結果を取得できませんでした"
        
        # 長すぎる場合は要約
        if len(text) > 100:
            # 最初の文または重要な部分を抽出
            sentences = text.replace('。', '。\n').split('\n')
            if sentences:
                return sentences[0] + "。"
        
        return text
    
    def on_wakeword_detected(self):
        """ウェイクワード検出時の処理"""
        current_time = time.time()
        
        # 連続検出防止
        if current_time - self.last_processing_time < 3.0:
            print("⏳ Cooldown active, ignoring wakeword")
            return
        
        print("\n🎯 WAKEWORD DETECTED!")
        print("🤖 PiVot Smart Assistant Activated")
        
        speak("はい、何でしょうか？")
        
        # 非同期でビジュアル推論を実行
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            # 既にループが動いている場合はタスクを作成
            asyncio.create_task(self.process_visual_query())
        else:
            # ループが動いていない場合は実行
            loop.run_until_complete(self.process_visual_query())
    
    async def check_systems(self):
        """システム状態確認"""
        print("\n🔍 System Status Check:")
        print("-" * 30)
        
        # NPU状態確認
        try:
            npu_status = await self.pivot_client.check_npu_status()
            npu_available = npu_status.get('npu_available', False)
            print(f"🧠 NPU Server: {'✅ Available' if npu_available else '❌ Unavailable'}")
        except Exception as e:
            print(f"🧠 NPU Server: ❌ Connection Error ({e})")
        
        # カメラ状態確認
        camera_status = "✅ Ready" if not self.camera.mock_mode else "⚠️ Mock Mode"
        print(f"📷 Camera: {camera_status}")
        
        # アップロードサーバー状態確認
        print(f"📤 Upload Server: {'✅ Running' if self.upload_server_thread and self.upload_server_thread.is_alive() else '❌ Stopped'}")
        
        print("-" * 30)
    
    def run(self):
        """メインシステムを実行"""
        print("🚀 Starting PiVot Smart Voice Assistant...")
        
        # 1. アップロードサーバー起動
        self.start_upload_server()
        
        # 2. VOICEVOX起動
        self.start_voicevox_engine()
        
        # 3. システム状態確認
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.check_systems())
        
        # 4. メインアシスタントループ開始
        print("\n🎤 Listening for wakeword: 'taro_tsuu'")
        print("💡 Say the wakeword to activate visual AI assistant!")
        print("🛑 Press Ctrl+C to exit")
        print("=" * 60)
        
        try:
            # ウェイクワード検出開始
            self.wakeword_detector.listen(self.on_wakeword_detected)
            
        except KeyboardInterrupt:
            print("\n🛑 Shutting down PiVot Smart Assistant...")
            self.cleanup()
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            self.cleanup()
    
    def cleanup(self):
        """システムクリーンアップ"""
        print("🧹 Cleaning up resources...")
        
        # カメラクリーンアップ
        if self.camera:
            self.camera.cleanup()
        
        print("✅ PiVot Smart Assistant stopped")

# メイン実行
def main():
    """メイン関数"""
    assistant = PiVotSmartAssistant()
    assistant.run()

if __name__ == "__main__":
    main()