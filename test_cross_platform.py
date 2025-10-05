#!/usr/bin/env python3
"""
Cross-Platform Environment Test
Linux (PiVot) ⟷ Windows (PiVot-Server) 環境テスト
"""

import asyncio
import requests
import sys
import os
import time
from config import PIVOT_SERVER_URL, IMAGE_UPLOAD_SERVER_URL, WINDOWS_PC_IP

async def test_network_connectivity():
    """ネットワーク接続テスト"""
    print("🌐 Testing Network Connectivity...")
    print(f"   Target: Windows PC at {WINDOWS_PC_IP}")
    
    # ping テスト
    try:
        import subprocess
        result = subprocess.run(['ping', '-c', '3', WINDOWS_PC_IP], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("   ✅ Ping successful")
            return True
        else:
            print("   ❌ Ping failed")
            return False
    except Exception as e:
        print(f"   ❌ Ping error: {e}")
        return False

async def test_pivot_server_connection():
    """PiVot-Server 接続テスト"""
    print("🧠 Testing PiVot-Server Connection...")
    print(f"   URL: {PIVOT_SERVER_URL}")
    
    try:
        # ヘルスチェック
        response = requests.get(f"{PIVOT_SERVER_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("   ✅ PiVot-Server connection successful")
            print(f"   📊 Server Status: {data}")
            return True
        else:
            print(f"   ❌ Server responded with status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection refused - server not running?")
        return False
    except requests.exceptions.Timeout:
        print("   ❌ Connection timeout")
        return False
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return False

async def test_image_upload_server():
    """画像アップロードサーバーテスト"""
    print("📤 Testing Image Upload Server...")
    print(f"   URL: {IMAGE_UPLOAD_SERVER_URL}")
    
    try:
        response = requests.get(f"{IMAGE_UPLOAD_SERVER_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Upload server connection successful")
            print(f"   📊 Server Status: {data}")
            return True
        else:
            print(f"   ❌ Server responded with status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection refused - upload server not running?")
        return False
    except requests.exceptions.Timeout:
        print("   ❌ Connection timeout")
        return False
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return False

def test_local_components():
    """ローカルコンポーネントテスト"""
    print("🔧 Testing Local Components...")
    
    # カメラモジュールテスト
    try:
        from s_compornents.pi_camera_controller import PiCameraController
        camera = PiCameraController(mock_mode=True)  # テストモード
        print("   ✅ Camera controller imported successfully")
        camera_ok = True
    except Exception as e:
        print(f"   ❌ Camera controller error: {e}")
        camera_ok = False
    
    # 音声モジュールテスト
    try:
        from s_compornents.voice import speak
        print("   ✅ Voice synthesis module imported successfully")
        voice_ok = True
    except Exception as e:
        print(f"   ❌ Voice synthesis error: {e}")
        voice_ok = False
    
    # ウェイクワードモジュールテスト
    try:
        from s_compornents.wakeword_detect_ext import WakewordDetector
        print("   ✅ Wakeword detector imported successfully")
        wakeword_ok = True
    except Exception as e:
        print(f"   ❌ Wakeword detector error: {e}")
        wakeword_ok = False
    
    return camera_ok and voice_ok and wakeword_ok

async def test_full_pipeline_simulation():
    """フルパイプラインシミュレーションテスト"""
    print("🚀 Testing Full Pipeline Simulation...")
    
    try:
        # 1. カメラシミュレーション
        from s_compornents.pi_camera_controller import PiCameraController
        camera = PiCameraController(mock_mode=True)
        image_path, image_id = camera.capture_image("test")
        print(f"   ✅ Mock image captured: {image_id}")
        
        # 2. クライアント接続テスト
        from s_compornents.pivot_server_client import PiVotServerClient
        client = PiVotServerClient()
        
        # 3. NPU状態確認
        npu_status = await client.check_npu_status()
        if npu_status.get('npu_available'):
            print("   ✅ NPU server is ready")
        else:
            print("   ⚠️ NPU server not ready but connection OK")
        
        print("   ✅ Pipeline simulation completed")
        return True
        
    except Exception as e:
        print(f"   ❌ Pipeline simulation failed: {e}")
        return False

def print_environment_info():
    """環境情報を表示"""
    print("📋 Environment Information:")
    print("=" * 50)
    print(f"🐧 Platform: {sys.platform}")
    print(f"🐍 Python: {sys.version}")
    print(f"📍 Working Directory: {os.getcwd()}")
    print(f"🖥️ Windows PC IP: {WINDOWS_PC_IP}")
    print(f"🔗 PiVot-Server: {PIVOT_SERVER_URL}")
    print(f"📤 Upload Server: {IMAGE_UPLOAD_SERVER_URL}")
    print("=" * 50)

async def main():
    """メインテスト実行"""
    print("🧪 PiVot Cross-Platform Environment Test")
    print("Environment: PiVot(Linux) ⟷ PiVot-Server(Windows)")
    print("=" * 60)
    
    # 環境情報表示
    print_environment_info()
    
    # テスト実行
    tests = [
        ("Network Connectivity", test_network_connectivity()),
        ("PiVot-Server Connection", test_pivot_server_connection()),
        ("Image Upload Server", test_image_upload_server()),
        ("Local Components", test_local_components()),
        ("Full Pipeline Simulation", test_full_pipeline_simulation())
    ]
    
    results = []
    
    for test_name, test_task in tests:
        print(f"\n🔍 Running {test_name}...")
        try:
            if asyncio.iscoroutine(test_task):
                result = await test_task
            else:
                result = test_task
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test error: {e}")
            results.append((test_name, False))
        
        time.sleep(1)  # テスト間の待機
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 Cross-Platform Test Results:")
    print("-" * 40)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:30} {status}")
        if result:
            passed += 1
    
    print("-" * 40)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Cross-platform system is ready!")
        print("\n💡 You can now start the PiVot Assistant:")
        print("   ./start_pivot_assistant.sh")
    elif passed >= total * 0.7:  # 70%以上で条件付き成功
        print("⚠️ Most tests passed. System may work with minor issues.")
        print(f"\n📝 Failed tests: {total - passed}")
        print("💡 Check network connectivity and server status.")
    else:
        print("❌ Multiple tests failed. System configuration needed.")
        print(f"\n📝 Failed tests: {total - passed}")
        print("💡 Please check:")
        print("   1. Windows PC PiVot-Server is running")
        print("   2. Network connectivity between devices")
        print("   3. Firewall settings on Windows PC")
        print("   4. config.py has correct Windows PC IP")
    
    print("=" * 60)
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)