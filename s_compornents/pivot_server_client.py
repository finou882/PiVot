"""
PiVot-Server Integration Client
PiVot-ServerのNPU推論APIとの連携クライアント
"""

import os
import aiohttp
import asyncio
import json
from typing import Dict, Any, Optional, Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class PiVotServerClient:
    """PiVot-Server NPU推論クライアント"""
    
    def __init__(self, 
                 server_url: str = "http://192.168.1.100:8001",  # Windows PCのIPアドレス
                 timeout: int = 30,
                 image_upload_server: str = "http://192.168.1.100:8002"):  # Windows PCのIPアドレス
        """
        Args:
            server_url: PiVot-ServerのURL（NPU推論用）
            timeout: リクエストタイムアウト（秒）
            image_upload_server: 画像アップロードサーバーのURL
        """
        self.server_url = server_url.rstrip('/')
        self.image_upload_server = image_upload_server.rstrip('/')
        self.timeout = timeout
        
        # APIエンドポイント
        self.endpoints = {
            'voice_infer': f"{self.server_url}/voice/infer",
            'voice_quick': f"{self.server_url}/voice/quick", 
            'npu_status': f"{self.server_url}/npu/status",
            'system_health': f"{self.server_url}/health"
        }
        
        print(f"✅ PiVot-Server Client initialized")
        print(f"   NPU Server: {self.server_url}")
        print(f"   Upload Server: {self.image_upload_server}")
    
    async def upload_image_to_server(self, image_path: str, image_id: str) -> bool:
        """
        画像をアップロードサーバーに送信
        
        Args:
            image_path: ローカル画像パス
            image_id: 画像ID
            
        Returns:
            bool: アップロード成功フラグ
        """
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found: {image_path}")
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                # マルチパートフォームデータとして送信
                with open(image_path, 'rb') as f:
                    data = aiohttp.FormData()
                    data.add_field('image', f, filename=f"{image_id}.jpg", content_type='image/jpeg')
                    data.add_field('image_id', image_id)
                    
                    upload_url = f"{self.image_upload_server}/upload/{image_id}"
                    
                    async with session.post(upload_url, data=data) as response:
                        if response.status == 200:
                            result = await response.json()
                            print(f"✅ Image uploaded: {image_id}")
                            return True
                        else:
                            error_text = await response.text()
                            logger.error(f"❌ Upload failed ({response.status}): {error_text}")
                            return False
                            
        except Exception as e:
            logger.error(f"❌ Image upload error: {e}")
            return False
    
    async def voice_inference_with_image_id(self, 
                                          image_id: str, 
                                          query: str = "この画像について説明してください") -> Dict[str, Any]:
        """
        画像IDを使ってNPU音声推論を実行
        
        Args:
            image_id: アップロード済み画像ID
            query: 質問文
            
        Returns:
            Dict: NPU推論結果
        """
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                # リクエストデータ
                payload = {
                    "image_id": image_id,
                    "text": query,
                    "image_base_url": self.image_upload_server
                }
                
                # NPU推論リクエスト
                async with session.post(
                    self.endpoints['voice_infer'], 
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ NPU inference successful")
                        print(f"   Image ID: {image_id}")
                        print(f"   Query: {query}")
                        print(f"   Response: {result.get('response', 'No response')}")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ NPU inference failed ({response.status}): {error_text}")
                        return {
                            "success": False,
                            "error": f"Server error: {response.status}",
                            "response": "推論に失敗しました"
                        }
                        
        except asyncio.TimeoutError:
            logger.error(f"❌ NPU inference timeout")
            return {
                "success": False,
                "error": "Timeout",
                "response": "推論がタイムアウトしました"
            }
        except Exception as e:
            logger.error(f"❌ NPU inference error: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "推論中にエラーが発生しました"
            }
    
    async def quick_voice_inference(self, 
                                   image_id: str, 
                                   query: str = "簡潔に説明して") -> str:
        """
        高速音声推論（レスポンステキストのみ取得）
        
        Args:
            image_id: 画像ID
            query: 質問文
            
        Returns:
            str: 推論結果テキスト
        """
        try:
            result = await self.voice_inference_with_image_id(image_id, query)
            return result.get('response', '推論に失敗しました')
        except Exception as e:
            logger.error(f"❌ Quick inference error: {e}")
            return "推論中にエラーが発生しました"
    
    async def check_npu_status(self) -> Dict[str, Any]:
        """NPU状態確認"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(self.endpoints['npu_status']) as response:
                    if response.status == 200:
                        status = await response.json()
                        print(f"✅ NPU Status: {status.get('npu_available', 'Unknown')}")
                        return status
                    else:
                        return {"npu_available": False, "error": f"Status check failed: {response.status}"}
                        
        except Exception as e:
            logger.error(f"❌ NPU status check error: {e}")
            return {"npu_available": False, "error": str(e)}
    
    async def full_pipeline(self, 
                           image_path: str, 
                           image_id: str,
                           query: str = "この画像に何が写っていますか？") -> Tuple[bool, str]:
        """
        完全パイプライン: 画像アップロード → NPU推論
        
        Args:
            image_path: ローカル画像パス
            image_id: 画像ID
            query: 質問文
            
        Returns:
            Tuple[success, response_text]: 成功フラグと応答テキスト
        """
        try:
            print(f"🚀 Starting full pipeline for image: {image_id}")
            
            # 1. 画像アップロード
            print("📤 Step 1: Uploading image...")
            upload_success = await self.upload_image_to_server(image_path, image_id)
            if not upload_success:
                return False, "画像のアップロードに失敗しました"
            
            # 少し待機（サーバー処理時間考慮）
            await asyncio.sleep(0.5)
            
            # 2. NPU推論実行
            print("🧠 Step 2: NPU inference...")
            response_text = await self.quick_voice_inference(image_id, query)
            
            print(f"✅ Pipeline completed successfully")
            return True, response_text
            
        except Exception as e:
            logger.error(f"❌ Full pipeline error: {e}")
            return False, f"パイプライン実行中にエラーが発生しました: {e}"

# デフォルトクライアントインスタンス
default_client = PiVotServerClient()

# テスト関数
async def test_client():
    """クライアントテスト"""
    print("🔗 Testing PiVot-Server Client...")
    
    client = PiVotServerClient()
    
    try:
        # NPU状態確認テスト
        status = await client.check_npu_status()
        print(f"NPU Status: {status}")
        
        # TODO: 実際の画像でテストする場合はここを有効化
        # image_path = "test_image.jpg"
        # image_id = "test_123456"
        # success, response = await client.full_pipeline(image_path, image_id)
        # print(f"Pipeline result: {success}, {response}")
        
    except Exception as e:
        print(f"❌ Client test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_client())