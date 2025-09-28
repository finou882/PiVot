"""
Simple Image Upload Server
PiVot-Server用の画像アップロード&配信サーバー
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import logging

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

logger = logging.getLogger(__name__)

class ImageUploadServer:
    """画像アップロード&配信サーバー"""
    
    def __init__(self, 
                 upload_dir: str = "./uploaded_images",
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 allowed_extensions: list = None):
        """
        Args:
            upload_dir: アップロード画像保存ディレクトリ
            max_file_size: 最大ファイルサイズ（バイト）
            allowed_extensions: 許可する拡張子
        """
        self.upload_dir = Path(upload_dir)
        self.max_file_size = max_file_size
        self.allowed_extensions = allowed_extensions or ['.jpg', '.jpeg', '.png', '.bmp']
        
        # アップロードディレクトリを作成
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # FastAPIアプリケーション作成
        self.app = FastAPI(
            title="📤 PiVot Image Upload Server",
            version="1.0.0",
            description="""
## 画像アップロード&配信サーバー

**PiVot-Server用の軽量画像ハンドリングサーバー**

### 主な機能
- 📤 画像アップロード（マルチパート対応）
- 📥 画像配信（HTTP GET）
- 🗂️ アップロード履歴管理
- 🔍 画像情報取得

### 対応形式
- JPEG (.jpg, .jpeg)
- PNG (.png) 
- BMP (.bmp)
- 最大ファイルサイズ: 10MB
""",
            openapi_tags=[
                {
                    "name": "Upload",
                    "description": "画像アップロード関連エンドポイント"
                },
                {
                    "name": "Download",
                    "description": "画像配信・取得エンドポイント"
                },
                {
                    "name": "Management",
                    "description": "サーバー管理・情報取得エンドポイント"
                }
            ]
        )
        
        # CORS設定
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # ルート設定
        self._setup_routes()
        
        print(f"📤 Image Upload Server initialized")
        print(f"   Upload directory: {self.upload_dir}")
        print(f"   Max file size: {self.max_file_size / (1024*1024):.1f}MB")
    
    def _setup_routes(self):
        """APIルートを設定"""
        
        @self.app.get("/", tags=["Management"])
        async def root():
            """サーバー情報"""
            return {
                "service": "PiVot Image Upload Server",
                "version": "1.0.0",
                "upload_dir": str(self.upload_dir),
                "max_file_size_mb": self.max_file_size / (1024*1024),
                "allowed_extensions": self.allowed_extensions,
                "uploaded_images": len(list(self.upload_dir.glob("*.*")))
            }
        
        @self.app.get("/health", tags=["Management"])
        async def health_check():
            """ヘルスチェック"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "upload_dir_exists": self.upload_dir.exists(),
                "upload_dir_writable": os.access(self.upload_dir, os.W_OK)
            }
        
        @self.app.post("/upload/{image_id}", tags=["Upload"])
        async def upload_image(
            image_id: str,
            image: UploadFile = File(...),
            metadata: str = Form(None)
        ):
            """
            画像をアップロード
            
            - **image_id**: 画像の一意ID（年月日時分秒推奨）
            - **image**: アップロードする画像ファイル
            - **metadata**: オプションのメタデータ（JSON文字列）
            """
            try:
                # ファイルサイズチェック
                content = await image.read()
                if len(content) > self.max_file_size:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Max size: {self.max_file_size / (1024*1024):.1f}MB"
                    )
                
                # 拡張子チェック
                file_ext = Path(image.filename).suffix.lower()
                if file_ext not in self.allowed_extensions:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unsupported file type. Allowed: {self.allowed_extensions}"
                    )
                
                # ファイル名を決定（IDベース）
                filename = f"{image_id}{file_ext}"
                file_path = self.upload_dir / filename
                
                # ファイル保存
                with open(file_path, "wb") as f:
                    f.write(content)
                
                # メタデータ保存（オプション）
                if metadata:
                    metadata_path = self.upload_dir / f"{image_id}.json"
                    with open(metadata_path, "w", encoding="utf-8") as f:
                        f.write(metadata)
                
                print(f"✅ Image uploaded: {filename} ({len(content)} bytes)")
                
                return {
                    "success": True,
                    "image_id": image_id,
                    "filename": filename,
                    "size_bytes": len(content),
                    "url": f"/image/{image_id}",
                    "upload_time": datetime.now().isoformat()
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"❌ Upload error: {e}")
                raise HTTPException(status_code=500, detail=f"Upload failed: {e}")
        
        @self.app.get("/image/{image_id}", tags=["Download"])
        async def get_image(image_id: str):
            """
            画像を取得
            
            - **image_id**: 取得する画像のID
            """
            try:
                # 対応する画像ファイルを検索
                for ext in self.allowed_extensions:
                    image_path = self.upload_dir / f"{image_id}{ext}"
                    if image_path.exists():
                        return FileResponse(
                            path=str(image_path),
                            media_type=f"image/{ext[1:]}",
                            filename=f"{image_id}{ext}"
                        )
                
                # ファイルが見つからない場合
                raise HTTPException(status_code=404, detail=f"Image not found: {image_id}")
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"❌ Image retrieval error: {e}")
                raise HTTPException(status_code=500, detail=f"Retrieval failed: {e}")
        
        @self.app.get("/images", tags=["Management"])
        async def list_images():
            """アップロード済み画像一覧"""
            try:
                images = []
                for ext in self.allowed_extensions:
                    for image_path in self.upload_dir.glob(f"*{ext}"):
                        stat = image_path.stat()
                        image_id = image_path.stem
                        images.append({
                            "image_id": image_id,
                            "filename": image_path.name,
                            "size_bytes": stat.st_size,
                            "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                            "url": f"/image/{image_id}"
                        })
                
                return {
                    "total": len(images),
                    "images": sorted(images, key=lambda x: x["created_time"], reverse=True)
                }
                
            except Exception as e:
                logger.error(f"❌ Image list error: {e}")
                raise HTTPException(status_code=500, detail=f"List retrieval failed: {e}")
        
        @self.app.delete("/image/{image_id}", tags=["Management"])
        async def delete_image(image_id: str):
            """
            画像を削除
            
            - **image_id**: 削除する画像のID
            """
            try:
                deleted_files = []
                
                # 画像ファイルを削除
                for ext in self.allowed_extensions:
                    image_path = self.upload_dir / f"{image_id}{ext}"
                    if image_path.exists():
                        image_path.unlink()
                        deleted_files.append(f"{image_id}{ext}")
                
                # メタデータファイルも削除
                metadata_path = self.upload_dir / f"{image_id}.json"
                if metadata_path.exists():
                    metadata_path.unlink()
                    deleted_files.append(f"{image_id}.json")
                
                if deleted_files:
                    print(f"🗑️ Files deleted: {deleted_files}")
                    return {
                        "success": True,
                        "image_id": image_id,
                        "deleted_files": deleted_files
                    }
                else:
                    raise HTTPException(status_code=404, detail=f"Image not found: {image_id}")
                    
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"❌ Image deletion error: {e}")
                raise HTTPException(status_code=500, detail=f"Deletion failed: {e}")
    
    def start_server(self, host: str = "0.0.0.0", port: int = 8002, reload: bool = False):
        """サーバーを開始"""
        print(f"🚀 Starting Image Upload Server on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port, reload=reload)

# デフォルトサーバーインスタンス
default_server = ImageUploadServer()

def start_upload_server():
    """アップロードサーバーを開始"""
    server = ImageUploadServer()
    server.start_server()

if __name__ == "__main__":
    start_upload_server()