#!/usr/bin/env python3
"""
PiVot Smart Assistant System Test
システム統合テストスクリプト
"""

import asyncio
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from s_compornents.pi_camera_controller import PiCameraController
from s_compornents.pivot_server_client import PiVotServerClient
from s_compornents.voice import speak

async def test_camera():
    """カメラテスト"""
    print("📷 Testing Raspberry Pi Camera...")
    camera = PiCameraController(mock_mode=True)  # テスト用モック
    
    try:
        image_path, image_id = camera.capture_image("test")
        print(f"✅ Camera test passed: {image_id}")
        return image_path, image_id
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
        return None, None

async def test_pivot_server_connection():
    """PiVot-Server接続テスト"""
    print("🧠 Testing PiVot-Server connection...")
    client = PiVotServerClient()
    
    try:
        status = await client.check_npu_status()
        if status.get('npu_available'):
            print("✅ PiVot-Server connection test passed")
            return True
        else:
            print("⚠️ PiVot-Server available but NPU not ready")
            return False
    except Exception as e:
        print(f"❌ PiVot-Server connection test failed: {e}")
        return False

async def test_full_pipeline():
    """フルパイプラインテスト"""
    print("🚀 Testing full pipeline...")
    
    # カメラテスト
    camera = PiCameraController(mock_mode=True)
    image_path, image_id = camera.capture_image("pipeline_test")
    
    if not image_path:
        print("❌ Full pipeline test failed - camera error")
        return False
    
    # PiVot-Server統合テスト
    client = PiVotServerClient()
    
    try:
        success, response = await client.full_pipeline(
            image_path=image_path,
            image_id=image_id,
            query="テスト画像です"
        )
        
        if success:
            print(f"✅ Full pipeline test passed: {response}")
            return True
        else:
            print(f"❌ Full pipeline test failed: {response}")
            return False
            
    except Exception as e:
        print(f"❌ Full pipeline test failed: {e}")
        return False

def test_voice():
    """音声合成テスト"""
    print("🔊 Testing voice synthesis...")
    try:
        speak("PiVot スマート音声アシスタントのテストです")
        print("✅ Voice test passed")
        return True
    except Exception as e:
        print(f"❌ Voice test failed: {e}")
        return False

async def main():
    """メインテスト実行"""
    print("🧪 PiVot Smart Assistant System Test")
    print("=" * 50)
    
    tests = [
        ("Camera", test_camera),
        ("PiVot-Server Connection", test_pivot_server_connection),
        ("Full Pipeline", test_full_pipeline),
        ("Voice Synthesis", lambda: test_voice())
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test error: {e}")
            results.append((test_name, False))
        
        time.sleep(1)  # テスト間の待機
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("-" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:25} {status}")
        if result:
            passed += 1
    
    print("-" * 30)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System ready for use.")
        return True
    else:
        print("⚠️ Some tests failed. Check system configuration.")
        return False

if __name__ == "__main__":
    asyncio.run(main())