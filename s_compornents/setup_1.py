"""
PiVot Smart Assistant - Complete Setup Script
PiVot スマート音声アシスタント 完全セットアップ
"""

import subprocess
import sys
import os
import platform
from pathlib import Path

def install_requirements():
    """requirements.txt から依存関係をインストール"""
    print("📦 Installing Python dependencies...")
    
    # requirements.txt の絶対パスを取得
    requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    
    try:
        # pip install を実行
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", requirements_path
        ], check=True, capture_output=True, text=True)
        
        print("✅ Python dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Python dependencies: {e}")
        print(f"   stderr: {e.stderr}")
        return False

def install_system_dependencies():
    """システム依存関係をインストール"""
    print("🔧 Installing system dependencies...")
    
    system = platform.system().lower()
    
    if system == "linux":
        # Raspberry Pi / Linux用
        commands = [
            # システムパッケージ更新
            ["sudo", "apt", "update"],
            
            # 音声・カメラ関連パッケージ
            ["sudo", "apt", "install", "-y", 
             "python3-pyaudio", "portaudio19-dev", "python3-dev",
             "libasound2-dev", "pulseaudio", "alsa-utils",
             "python3-picamera", "libraspberrypi-bin"],
            
            # 追加の音声処理パッケージ
            ["sudo", "apt", "install", "-y",
             "espeak", "espeak-data", "libespeak-dev", "festival"],
             
            # HTTPクライアント・サーバー関連
            ["sudo", "apt", "install", "-y", "curl", "wget", "netcat"]
        ]
        
        for cmd in commands:
            try:
                print(f"   Running: {' '.join(cmd)}")
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as e:
                print(f"   ⚠️ Command failed (continuing): {e}")
                
        print("✅ Linux system dependencies installed")
        
    elif system == "windows":
        # Windows用（主にPython依存関係のみ）
        print("   Windows system - using Python packages only")
        
    else:
        print(f"   ⚠️ Unsupported system: {system}")
    
    return True

def setup_audio_permissions():
    """音声デバイスのアクセス権限を設定"""
    print("🎤 Setting up audio permissions...")
    
    system = platform.system().lower()
    
    if system == "linux":
        try:
            # ユーザーを audio グループに追加
            username = os.getenv("USER")
            subprocess.run(["sudo", "usermod", "-a", "-G", "audio", username], check=True)
            print("✅ Audio permissions configured")
            print("   ⚠️ Please logout and login again for audio permissions to take effect")
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️ Could not set audio permissions: {e}")
    
    return True

def setup_camera_permissions():
    """Raspberry Pi カメラのアクセス権限を設定"""
    print("📷 Setting up camera permissions...")
    
    system = platform.system().lower()
    
    if system == "linux":
        try:
            # ユーザーを video グループに追加
            username = os.getenv("USER")
            subprocess.run(["sudo", "usermod", "-a", "-G", "video", username], check=True)
            
            # カメラの有効化確認
            print("   💡 To enable Pi Camera, run: sudo raspi-config")
            print("   💡 Go to Interface Options → Camera → Enable")
            print("✅ Camera permissions configured")
            
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️ Could not set camera permissions: {e}")
    
    return True

def create_directories():
    """必要なディレクトリを作成"""
    print("📁 Creating necessary directories...")
    
    directories = [
        "captured_images",
        "uploaded_images", 
        "logs"
    ]
    
    base_path = Path(__file__).parent.parent  # PiVot/ ディレクトリ
    
    for dir_name in directories:
        dir_path = base_path / dir_name
        dir_path.mkdir(exist_ok=True)
        print(f"   ✅ Created: {dir_path}")
    
    return True

def test_installations():
    """インストールをテスト"""
    print("🧪 Testing installations...")
    
    # 重要なモジュールのインポートテスト
    test_modules = [
        ("pyaudio", "PyAudio (audio input)"),
        ("openwakeword", "OpenWakeWord (wake word detection)"),
        ("aiohttp", "aiohttp (HTTP client)"),
        ("fastapi", "FastAPI (web framework)"),
        ("PIL", "Pillow (image processing)"),
        ("requests", "requests (HTTP requests)")
    ]
    
    failed_modules = []
    
    for module_name, description in test_modules:
        try:
            __import__(module_name)
            print(f"   ✅ {description}")
        except ImportError:
            print(f"   ❌ {description}")
            failed_modules.append(module_name)
    
    if failed_modules:
        print(f"⚠️ Failed to import: {', '.join(failed_modules)}")
        return False
    else:
        print("✅ All critical modules imported successfully")
        return True

def main():
    """メインセットアップ実行"""
    print("🚀 PiVot Smart Assistant - Complete Setup")
    print("=" * 60)
    print(f"🐧 Platform: {platform.system()} {platform.release()}")
    print(f"🐍 Python: {sys.version}")
    print("=" * 60)
    
    setup_steps = [
        ("System Dependencies", install_system_dependencies),
        ("Python Dependencies", install_requirements),
        ("Audio Permissions", setup_audio_permissions), 
        ("Camera Permissions", setup_camera_permissions),
        ("Directory Creation", create_directories),
        ("Installation Test", test_installations)
    ]
    
    failed_steps = []
    
    for step_name, step_func in setup_steps:
        print(f"\n🔧 {step_name}...")
        try:
            success = step_func()
            if not success:
                failed_steps.append(step_name)
        except Exception as e:
            print(f"❌ {step_name} failed: {e}")
            failed_steps.append(step_name)
    
    # セットアップ結果サマリー
    print("\n" + "=" * 60)
    print("📊 Setup Results Summary:")
    print("-" * 40)
    
    total_steps = len(setup_steps)
    passed_steps = total_steps - len(failed_steps)
    
    if not failed_steps:
        print("🎉 All setup steps completed successfully!")
        print("\n✅ PiVot Smart Assistant is ready to use!")
        print("\n🚀 Next steps:")
        print("   1. Configure config.py with Windows PC IP address")
        print("   2. Run: python3 network_setup.py (to auto-detect Windows PC)")
        print("   3. Start PiVot-Server on Windows PC")
        print("   4. Run: ./start_pivot_assistant.sh")
        
    elif passed_steps >= total_steps * 0.8:  # 80%以上成功
        print(f"⚠️ Setup mostly completed ({passed_steps}/{total_steps} steps)")
        print(f"Failed steps: {', '.join(failed_steps)}")
        print("\n💡 System may work with minor issues. Try running anyway.")
        
    else:
        print(f"❌ Setup failed ({passed_steps}/{total_steps} steps completed)")
        print(f"Failed steps: {', '.join(failed_steps)}")
        print("\n💡 Please resolve the failed steps before using PiVot.")
    
    print("\n📋 Manual steps (if needed):")
    print("   • Enable Pi Camera: sudo raspi-config → Interface Options → Camera")
    print("   • Reboot after permissions change: sudo reboot")
    print("   • Test camera: raspistill -v -o test.jpg")
    print("   • Test audio: python3 s_compornents/rr.py")
    print("=" * 60)
    
    return len(failed_steps) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)