#!/usr/bin/env python3
"""
PiVot Audio Environment Detector and Fixer
Detects audio issues and provides solutions
"""

import sys
import subprocess
import os
from pathlib import Path

def run_command(cmd, capture=True, timeout=30):
    """Run command safely with error handling"""
    try:
        if capture:
            result = subprocess.run(cmd, shell=True, capture_output=True, 
                                  text=True, timeout=timeout)
            return result.returncode == 0, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, shell=True, timeout=timeout)
            return result.returncode == 0, "", ""
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def check_audio_environment():
    """Check current audio environment and issues"""
    print("🔍 Audio Environment Diagnosis")
    print("=" * 40)
    
    issues = []
    
    # Check if in conda
    conda_env = os.environ.get('CONDA_DEFAULT_ENV')
    if conda_env:
        print(f"📦 Conda Environment: {conda_env}")
        issues.append("Using conda environment (may cause library conflicts)")
    else:
        print("🐍 Using System Python")
    
    # Check Python version
    print(f"🐍 Python: {sys.version}")
    
    # Test PyAudio import
    try:
        import pyaudio
        print("✅ PyAudio: Import successful")
        try:
            p = pyaudio.PyAudio()
            device_count = p.get_device_count()
            print(f"✅ Audio Devices: {device_count} found")
            p.terminate()
        except Exception as e:
            print(f"⚠️ PyAudio: Device access failed - {e}")
            issues.append(f"PyAudio device access: {e}")
    except ImportError as e:
        print(f"❌ PyAudio: Import failed - {e}")
        issues.append(f"PyAudio import: {e}")
        
        # Check for GLIBCXX issue specifically
        if "GLIBCXX" in str(e):
            issues.append("GLIBCXX version mismatch (conda/system library conflict)")
    
    # Check system audio libraries
    success, stdout, stderr = run_command("pkg-config --exists portaudio-2.0")
    if success:
        print("✅ PortAudio: System library found")
    else:
        print("❌ PortAudio: System library missing")
        issues.append("PortAudio system library not installed")
    
    # Check ALSA
    success, stdout, stderr = run_command("aplay -l")
    if success:
        print("✅ ALSA: Working")
    else:
        print("⚠️ ALSA: Issues detected")
        issues.append("ALSA audio system issues")
    
    return issues

def suggest_solutions(issues):
    """Suggest solutions based on detected issues"""
    print(f"\n💡 Recommended Solutions")
    print("=" * 40)
    
    if any("conda" in issue.lower() for issue in issues):
        print("🔧 Conda Environment Issues:")
        print("   Solution 1 - Use system Python for audio:")
        print("     conda deactivate")
        print("     /usr/bin/python3 main.py")
        print()
        print("   Solution 2 - Fix conda libraries:")
        print("     bash fix_pyaudio.sh")
        print()
    
    if any("glibcxx" in issue.lower() for issue in issues):
        print("🔧 GLIBCXX Library Conflict:")
        print("   Solution - Create compatibility link:")
        print("     sudo ln -sf /usr/lib/aarch64-linux-gnu/libstdc++.so.6 $CONDA_PREFIX/lib/libstdc++.so.6")
        print()
    
    if any("portaudio" in issue.lower() for issue in issues):
        print("🔧 PortAudio Missing:")
        print("   sudo apt install -y portaudio19-dev python3-pyaudio")
        print()
    
    if any("pyaudio" in issue.lower() for issue in issues):
        print("🔧 PyAudio Installation:")
        print("   Method 1 - System package:")
        print("     sudo apt install -y python3-pyaudio")
        print()
        print("   Method 2 - Pip with system libs:")
        print("     pip3 install --user pyaudio --no-cache-dir")
        print()

def create_run_script():
    """Create a script that runs with system Python"""
    script_content = """#!/bin/bash
# Run PiVot with System Python (avoiding conda issues)

echo "🚀 Starting PiVot with System Python"
echo "===================================="

# Temporarily deactivate conda if active
if [[ "$CONDA_DEFAULT_ENV" != "" ]]; then
    echo "📦 Deactivating conda: $CONDA_DEFAULT_ENV"
    source deactivate 2>/dev/null || conda deactivate 2>/dev/null || true
fi

# Use system python
SYSTEM_PYTHON="/usr/bin/python3"

if [ -f "$SYSTEM_PYTHON" ]; then
    echo "🐍 Using system Python: $SYSTEM_PYTHON"
    
    # Check if system PyAudio is available
    if $SYSTEM_PYTHON -c "import pyaudio" 2>/dev/null; then
        echo "✅ System PyAudio available"
        exec $SYSTEM_PYTHON main.py "$@"
    else
        echo "❌ System PyAudio not available"
        echo "💡 Run: sudo apt install python3-pyaudio"
        echo "   Then try again"
        exit 1
    fi
else
    echo "❌ System Python not found at $SYSTEM_PYTHON"
    exit 1
fi
"""
    
    script_path = "run_system_python.sh"
    try:
        with open(script_path, 'w') as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        print(f"✅ Created {script_path}")
        print(f"   Usage: ./{script_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to create run script: {e}")
        return False

def main():
    print("🔧 PiVot Audio Environment Checker")
    print("=" * 50)
    
    issues = check_audio_environment()
    
    if issues:
        print(f"\n⚠️ Found {len(issues)} issues:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        
        suggest_solutions(issues)
        
        print("\n🛠️ Quick Fix Options:")
        print("   1. Run: bash fix_pyaudio.sh")
        print("   2. Use system Python: ./run_system_python.sh")
        print("   3. Manual setup following suggestions above")
        
        # Create helper script
        create_run_script()
        
    else:
        print("\n🎉 No audio issues detected!")
        print("✅ Your environment should work correctly")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()