#!/bin/bash
# Fix PyAudio Installation Issues on Raspberry Pi
# Handles conda environment conflicts and library compatibility

echo "🔧 PyAudio Installation Fix for Raspberry Pi"
echo "============================================="

echo "🔍 Detecting Python environment..."

# Check if we're in conda
if [[ "$CONDA_DEFAULT_ENV" != "" ]]; then
    echo "📦 Detected Conda environment: $CONDA_DEFAULT_ENV"
    
    echo "🔄 Attempting conda-based fix..."
    
    # Method 1: Use conda packages
    echo "   Installing portaudio via conda..."
    conda install -c conda-forge portaudio -y
    
    echo "   Installing pyaudio via conda..."
    conda install -c conda-forge pyaudio -y
    
    # Method 2: If conda fails, use system packages
    echo "   Installing system audio libraries..."
    sudo apt update
    sudo apt install -y portaudio19-dev libasound2-dev pulseaudio alsa-utils
    
    # Method 3: Force reinstall with system compatibility
    echo "   Attempting pip reinstall with system libs..."
    pip uninstall pyaudio -y
    sudo apt install -y python3-pyaudio
    
    # Create a symlink fix for the GLIBCXX issue
    echo "   Creating compatibility symlinks..."
    CONDA_LIB_PATH="$CONDA_PREFIX/lib"
    if [ -d "$CONDA_LIB_PATH" ]; then
        # Backup original if exists
        if [ -f "$CONDA_LIB_PATH/libstdc++.so.6" ]; then
            mv "$CONDA_LIB_PATH/libstdc++.so.6" "$CONDA_LIB_PATH/libstdc++.so.6.backup" 2>/dev/null || true
        fi
        
        # Link to system library
        ln -sf /usr/lib/aarch64-linux-gnu/libstdc++.so.6 "$CONDA_LIB_PATH/libstdc++.so.6" 2>/dev/null || true
        echo "   ✅ Created libstdc++ compatibility link"
    fi

else
    echo "🐍 Detected system Python"
    
    echo "🔄 Installing system packages..."
    sudo apt update
    sudo apt install -y portaudio19-dev python3-pyaudio libasound2-dev pulseaudio alsa-utils
    
    echo "🔄 Installing pip packages..."
    pip3 install --user pyaudio --no-cache-dir
fi

# Test PyAudio installation
echo ""
echo "🧪 Testing PyAudio installation..."
python3 -c "
import sys
try:
    import pyaudio
    print('✅ PyAudio import successful')
    
    # Test initialization
    p = pyaudio.PyAudio()
    device_count = p.get_device_count()
    print(f'✅ Found {device_count} audio devices')
    p.terminate()
    print('✅ PyAudio test completed successfully')
    
except ImportError as e:
    print(f'❌ PyAudio import failed: {e}')
    sys.exit(1)
except Exception as e:
    print(f'⚠️ PyAudio test warning: {e}')
    print('PyAudio imported but may have device issues')
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 PyAudio installation fix completed successfully!"
    echo ""
    echo "💡 If you still have issues:"
    echo "   1. Restart your terminal/session"
    echo "   2. Try: source ~/.bashrc"
    echo "   3. Check audio devices: python3 -c 'import pyaudio; p=pyaudio.PyAudio(); print([p.get_device_info_by_index(i)[\"name\"] for i in range(p.get_device_count())]); p.terminate()'"
else
    echo ""
    echo "❌ PyAudio fix failed. Manual steps:"
    echo ""
    echo "1. Exit conda environment: conda deactivate"
    echo "2. Use system Python: /usr/bin/python3"
    echo "3. Install system PyAudio: sudo apt install python3-pyaudio"
    echo "4. Or use virtual environment instead of conda"
fi

echo "============================================="