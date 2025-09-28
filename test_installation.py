#!/usr/bin/env python3
"""
PiVot Raspberry Pi Installation Test Script
PiVot Raspberry Pi インストール確認スクリプト

This script tests if all PiVot Raspberry Pi components are properly installed.
このスクリプトはPiVot Raspberry Pi のすべてのコンポーネントが正しくインストールされているかをテストします。
"""

import sys
import os
import subprocess
import importlib
import platform
from pathlib import Path

# Add parent directory to path to import main test functions
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def print_header(title):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print('='*60)

def test_package_import(package_name, optional=False):
    """Test if a package can be imported"""
    try:
        importlib.import_module(package_name)
        print(f"✅ {package_name}")
        return True
    except ImportError as e:
        if optional:
            print(f"⚠️  {package_name} (optional) - {str(e)}")
        else:
            print(f"❌ {package_name} - {str(e)}")
        return False

def test_python_version():
    """Test Python version compatibility"""
    print_header("Python Version Check")
    version = sys.version_info
    print(f"Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 8:
        print("✅ Python version is compatible (3.8+)")
        return True
    else:
        print("❌ Python version is too old (3.8+ required)")
        return False

def test_required_packages():
    """Test all required packages"""
    print_header("Required Packages Test")
    
    required_packages = [
        ('numpy', 'numpy'),
        ('opencv-python', 'cv2'),
        ('fastapi', 'fastapi'), 
        ('uvicorn', 'uvicorn'),
        ('requests', 'requests'),
        ('pillow', 'PIL')
    ]
    
    results = []
    for package, import_name in required_packages:
        results.append(test_package_import(import_name))
    
    return all(results)

def test_optional_packages():
    """Test optional packages"""
    print_header("Optional Packages Test")
    
    optional_packages = [
        ('pyaudio', 'Audio input/output'),
        ('picamera', 'Raspberry Pi Camera (Pi only)'),
        ('RPi.GPIO', 'GPIO control (Pi only)')
    ]
    
    for package, description in optional_packages:
        if package == 'picamera':
            # Try both picamera and picamera2
            try:
                importlib.import_module('picamera')
                print(f"✅ picamera - {description}")
            except ImportError:
                try:
                    importlib.import_module('picamera2')
                    print(f"✅ picamera2 - {description}")
                except ImportError:
                    print(f"⚠️  picamera/picamera2 - {description}")
        else:
            test_package_import(package, optional=True)

def test_system_info():
    """Display system information"""
    print_header("System Information")
    
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Processor: {platform.processor()}")
    
    # Check if running on Raspberry Pi
    try:
        with open('/proc/cpuinfo', 'r') as f:
            if 'Raspberry Pi' in f.read():
                print("🥧 Raspberry Pi detected")
    except FileNotFoundError:
        pass
    
    # Check available camera devices
    if platform.system() == "Linux":
        video_devices = list(Path('/dev').glob('video*'))
        if video_devices:
            print(f"📷 Camera devices: {[str(d) for d in video_devices]}")
        else:
            print("📷 No camera devices found")

def test_file_permissions():
    """Test file permissions"""
    print_header("File Permissions Test")
    
    current_dir = Path.cwd()
    
    # Test read permission
    if os.access(current_dir, os.R_OK):
        print("✅ Read permission: OK")
    else:
        print("❌ Read permission: Failed")
    
    # Test write permission
    if os.access(current_dir, os.W_OK):
        print("✅ Write permission: OK")
    else:
        print("❌ Write permission: Failed")
    
    # Test execute permission
    if os.access(current_dir, os.X_OK):
        print("✅ Execute permission: OK")
    else:
        print("❌ Execute permission: Failed")

def run_quick_functionality_test():
    """Run a quick functionality test"""
    print_header("Quick Functionality Test")
    
    try:
        # Test numpy
        import numpy as np
        arr = np.array([1, 2, 3])
        print(f"✅ NumPy: {arr.sum()}")
        
        # Test OpenCV
        import cv2
        print(f"✅ OpenCV: Version {cv2.__version__}")
        
        # Test FastAPI import
        from fastapi import FastAPI
        app = FastAPI()
        print("✅ FastAPI: Import OK")
        
        # Test requests
        import requests
        print("✅ Requests: Import OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Functionality test failed: {str(e)}")
        return False

def test_raspberry_pi_specific():
    """Test Raspberry Pi specific components"""
    print_header("Raspberry Pi Specific Tests")
    
    # Check if running on Raspberry Pi
    is_raspberry_pi = False
    try:
        with open('/proc/cpuinfo', 'r') as f:
            content = f.read()
            if 'Raspberry Pi' in content:
                is_raspberry_pi = True
                print("✅ Running on Raspberry Pi")
            else:
                print("⚠️  Not running on Raspberry Pi")
    except FileNotFoundError:
        print("⚠️  Cannot determine if running on Raspberry Pi")
    
    # Test camera access
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("✅ Camera access: Available")
            cap.release()
        else:
            print("⚠️  Camera access: Not available")
    except Exception as e:
        print(f"⚠️  Camera access test failed: {str(e)}")
    
    # Test GPIO access (if RPi.GPIO is available)
    try:
        import RPi.GPIO as GPIO
        print("✅ GPIO access: Available")
    except ImportError:
        print("⚠️  GPIO access: RPi.GPIO not installed")
    except Exception as e:
        print(f"⚠️  GPIO access: {str(e)}")
    
    return is_raspberry_pi

def test_pivot_specific_files():
    """Test PiVot specific files"""
    print_header("PiVot Files Test")
    
    pivot_files = [
        'camera.py',
        'pivot_func.py', 
        'taro_tsuu.py',
        'voice.py',
        'compornents/taro_tsuu.onnx',
        's_compornents/requirements.txt',
        '../config.py',
        '../network_setup.py',
        '../start_pivot_assistant.sh'
    ]
    
    found_files = 0
    for file_path in pivot_files:
        path = Path(file_path)
        if path.exists():
            print(f"✅ {file_path}: Found")
            found_files += 1
        else:
            print(f"⚠️  {file_path}: Not found")
    
    return found_files / len(pivot_files)

def test_network_connection_to_server():
    """Test network connection to Windows PC server"""
    print_header("Network Connection to PiVot-Server Test")
    
    # Try to read Windows PC IP from config
    try:
        import sys
        sys.path.append('..')
        from config import WINDOWS_PC_IP
        print(f"Windows PC IP: {WINDOWS_PC_IP}")
        
        # Test connection
        import requests
        try:
            response = requests.get(f"http://{WINDOWS_PC_IP}:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ Connection to PiVot-Server: OK")
                return True
            else:
                print(f"⚠️  Connection to PiVot-Server: Status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection to PiVot-Server: {str(e)}")
            print("   Make sure PiVot-Server is running on Windows PC")
            return False
            
    except ImportError:
        print("⚠️  Cannot read Windows PC IP from config")
        print("   Run: python3 ../network_setup.py")
        return False
    except Exception as e:
        print(f"❌ Network test failed: {str(e)}")
        return False

def test_audio_system():
    """Test audio system"""
    print_header("Audio System Test")
    
    try:
        import pyaudio
        audio = pyaudio.PyAudio()
        
        # Check input devices
        input_devices = []
        output_devices = []
        
        for i in range(audio.get_device_count()):
            device_info = audio.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                input_devices.append(device_info['name'])
            if device_info['maxOutputChannels'] > 0:
                output_devices.append(device_info['name'])
        
        audio.terminate()
        
        print(f"✅ Audio input devices: {len(input_devices)}")
        print(f"✅ Audio output devices: {len(output_devices)}")
        
        return len(input_devices) > 0 and len(output_devices) > 0
        
    except ImportError:
        print("❌ PyAudio not installed")
        return False
    except Exception as e:
        print(f"❌ Audio test failed: {str(e)}")
        return False

def run_pivot_functionality_test():
    """Run PiVot specific functionality test"""
    print_header("PiVot Functionality Test")
    
    try:
        # Test wake word model loading
        if Path('compornents/taro_tsuu.onnx').exists():
            print("✅ Wake word model: Found")
        else:
            print("⚠️  Wake word model: Not found")
        
        # Test camera initialization
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    print("✅ Camera functionality: OK")
                    cap.release()
                    return True
                else:
                    print("⚠️  Camera functionality: Cannot capture")
                    cap.release()
                    return False
            else:
                print("⚠️  Camera functionality: Cannot open")
                return False
        except Exception as e:
            print(f"❌ Camera test failed: {str(e)}")
            return False
            
    except Exception as e:
        print(f"❌ PiVot functionality test failed: {str(e)}")
        return False

def main():
    """Main test function for PiVot Raspberry Pi"""
    print("🥧 PiVot Raspberry Pi Installation Test")
    print("======================================")
    print("This script will test your PiVot Raspberry Pi installation...")
    
    # Run basic tests
    results = {}
    results['python_version'] = test_python_version()
    results['required_packages'] = test_required_packages()
    results['functionality'] = run_quick_functionality_test()
    
    # PiVot specific tests
    results['raspberry_pi'] = test_raspberry_pi_specific()
    results['pivot_files'] = test_pivot_specific_files() > 0.8
    results['pivot_functionality'] = run_pivot_functionality_test()
    results['audio_system'] = test_audio_system()
    results['network_connection'] = test_network_connection_to_server()
    
    # Optional tests
    test_optional_packages()
    test_system_info()
    test_file_permissions()
    
    # Generate report
    print_header("PiVot Test Summary Report")
    
    passed = sum([1 for k, v in results.items() if v])
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed >= total * 0.8:
        print("\n🎉 PiVot Raspberry Pi is ready!")
        print("\nNext steps:")
        print("  1. Make sure Windows PC PiVot-Server is running")
        print("  2. Start PiVot: bash ../start_pivot_assistant.sh")
        print("  3. Say 'タロー通' to activate voice assistant")
    else:
        print("\n❌ Some tests failed. Please check your installation.")
        print("Run: bash setup_all.sh")
        print("Or check: ../TROUBLESHOOTING.md")
    
    # Exit with appropriate code
    sys.exit(0 if passed >= total * 0.8 else 1)

if __name__ == "__main__":
    main()