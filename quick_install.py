#!/usr/bin/env python3
"""
PiVot Quick Install - One Command Setup
ワンコマンド超簡単セットアップ
"""

import subprocess
import sys
import os
import platform
from pathlib import Path

def quick_install():
    """超簡単インストール"""
    print("🚀 PiVot Quick Install - One Command Setup")
    print("=" * 50)
    
    # プラットフォーム検出
    system = platform.system().lower()
    print(f"🖥️ Platform: {platform.system()}")
    
    if system == "linux":
        # Raspberry Pi / Linux用クイックインストール
        print("🐧 Linux/Raspberry Pi detected")
        return install_linux()
    elif system == "windows":
        # Windows用クイックインストール
        print("🖥️ Windows detected")
        return install_windows()
    else:
        print(f"❌ Unsupported platform: {system}")
        return False

def install_linux():
    """Linux/Raspberry Pi用インストール"""
    commands = [
        # 必須パッケージのインストール
        ["sudo", "apt", "update"],
        ["sudo", "apt", "install", "-y", "python3-pip", "git", "curl"],
        
        # PiVot依存関係
        ["pip3", "install", "--user", "openwakeword", "aiohttp", "fastapi", "uvicorn", "pillow", "requests", "asyncio"],
        
        # Raspberry Pi特有のパッケージ
        ["sudo", "apt", "install", "-y", "python3-pyaudio", "portaudio19-dev", "python3-picamera", "espeak"]
    ]
    
    for cmd in commands:
        print(f"▶️ Running: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True)
            print("   ✅ Success")
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️ Warning: {e}")
    
    print("\n✅ Linux/Raspberry Pi setup completed!")
    print("\n📝 Additional manual steps:")
    print("   1. Enable camera: sudo raspi-config → Interface → Camera → Enable")
    print("   2. Reboot: sudo reboot")
    print("   3. Configure Windows PC IP in config.py")
    
    return True

def install_windows():
    """Windows用インストール"""
    commands = [
        # PiVot依存関係
        ["pip", "install", "openvino", "transformers", "pillow", "fastapi", "uvicorn", "aiohttp", "requests", "numpy"]
    ]
    
    for cmd in commands:
        print(f"▶️ Running: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True)
            print("   ✅ Success")
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️ Warning: {e}")
    
    print("\n✅ Windows setup completed!")
    print("\n📝 Next steps:")
    print("   1. This PC will run PiVot-Server (NPU)")
    print("   2. Configure Raspberry Pi to connect to this PC")
    print("   3. Start PiVot-Server: python main_npu.py")
    
    return True

if __name__ == "__main__":
    try:
        success = quick_install()
        if success:
            print("\n🎉 PiVot Quick Install completed!")
            print("📚 Full documentation: https://github.com/finou882/PiVot")
        else:
            print("\n❌ Installation failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)