#!/bin/bash
# PiVot Smart Voice Assistant Startup Script
# Comprehensive startup with net# 4. Audio Device Check and Fix
echo "🎤 Checking audio devices..."

# Check PyAudio and devices using python3 -c
python3 -c "
import sys
try:
    import pyaudio
    p = pyaudio.PyAudio()
    device_count = p.get_device_count()
    print(f'   ✅ PyAudio working, found {device_count} devices')
    
    # Find suitable input devices
    suitable_devices = []
    for i in range(device_count):
        try:
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                suitable_devices.append((i, info['name'], info['maxInputChannels']))
                print(f'   📱 Device {i}: {info[\"name\"]} (channels: {info[\"maxInputChannels\"]})')
        except:
            continue
    
    if not suitable_devices:
        print('   ❌ No suitable input devices found')
        sys.exit(1)
    else:
        print(f'   ✅ Found {len(suitable_devices)} suitable input devices')
    
    p.terminate()
    
except ImportError as e:
    print(f'   ❌ PyAudio import failed: {e}')
    print('   💡 Try: bash fix_pyaudio.sh')
    sys.exit(1)
except Exception as e:
    print(f'   ❌ Audio device error: {e}')
    if 'Invalid number of channels' in str(e):
        print('   💡 Audio device configuration issue detected')
        print('   💡 Will attempt auto-fix...')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "🔧 Attempting audio device auto-fix..."
    
    # Try to fix audio device index in config.py
    python3 -c "
import re
try:
    with open('config.py', 'r') as f:
        content = f.read()
    
    # Find a working audio device
    import pyaudio
    p = pyaudio.PyAudio()
    working_device = None
    
    for i in range(p.get_device_count()):
        try:
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                # Test if device actually works
                test_stream = p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    input_device_index=i,
                    frames_per_buffer=1024
                )
                test_stream.close()
                working_device = i
                print(f'   ✅ Working device found: {i} ({info[\"name\"]})')
                break
        except:
            continue
    
    p.terminate()
    
    if working_device is not None:
        # Update config.py
        pattern = r'AUDIO_INPUT_DEVICE_INDEX\s*=\s*\d+'
        replacement = f'AUDIO_INPUT_DEVICE_INDEX = {working_device}'
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            with open('config.py', 'w') as f:
                f.write(content)
            print(f'   ✅ Updated config.py: AUDIO_INPUT_DEVICE_INDEX = {working_device}')
        else:
            print(f'   ⚠️ Could not find AUDIO_INPUT_DEVICE_INDEX in config.py')
    else:
        print('   ❌ No working audio devices found')
        
except Exception as e:
    print(f'   ⚠️ Auto-fix failed: {e}')
"
    
    echo "🔄 Continue anyway? (y/N): "
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "❌ Cannot proceed without working audio"
        exit 1
    fi
fi

# 5. Start PiVot Assistantork verification and error handling

echo "🤖 Starting PiVot Smart Voice Assistant System"
echo "Environment: PiVot(Linux) ⟷ PiVot-Server(Windows)"
echo "================================================"

# 1. Network Configuration Check
echo "🔍 Checking network configuration..."
if ! python3 network_setup.py; then
    echo "⚠️ Network configuration had issues, but continuing..."
fi

echo ""
echo "📝 Continue with current configuration? (y/N): "
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "❌ Setup cancelled by user"
    exit 1
fi

# 2. Load configuration
echo "🔧 Loading configuration..."
if [ -f "config.py" ]; then
    # Extract IP from config.py
    WINDOWS_PC_IP=$(python3 -c "
try:
    import config
    print(config.WINDOWS_PC_IP)
except Exception as e:
    print('192.168.1.100')  # fallback
")
    echo "   Windows PC IP: $WINDOWS_PC_IP"
else
    echo "❌ config.py not found!"
    exit 1
fi

# 3. Test PiVot-Server connectivity
echo "🧠 Checking PiVot-Server (Windows PC)..."
echo "   Windows PC IP: $WINDOWS_PC_IP"

# Test connectivity
SERVER_ACCESSIBLE=false
for port in 8000 8001; do
    if curl -s --connect-timeout 3 "http://$WINDOWS_PC_IP:$port/health" > /dev/null 2>&1 ||
       curl -s --connect-timeout 3 "http://$WINDOWS_PC_IP:$port/" > /dev/null 2>&1; then
        SERVER_ACCESSIBLE=true
        echo "   ✅ PiVot-Server accessible on port $port"
        break
    fi
done

if [ "$SERVER_ACCESSIBLE" = false ]; then
    echo "   ❌ PiVot-Server not accessible"
    echo "   💡 Make sure PiVot-Server is running on Windows PC"
    echo "   💡 Check IP address and firewall settings"
    echo ""
    echo "🔄 Continue anyway? (y/N): "
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "❌ Cannot proceed without server connection"
        exit 1
    fi
fi

# 4. Start VoiceVox TTS Engine
echo "🔊 Starting VoiceVox TTS Engine..."
if [ -f "./s_compornents/compornents/voicevox/run" ]; then
    # VoiceVoxをバックグラウンドで起動
    ./s_compornents/compornents/voicevox/run &
    VOICEVOX_PID=$!
    echo "   VoiceVox PID: $VOICEVOX_PID"
    
    # VoiceVoxの起動を少し待つ
    sleep 5
    
    # VoiceVoxが起動しているかチェック
    if kill -0 $VOICEVOX_PID 2>/dev/null; then
        echo "   ✅ VoiceVox TTS Engine started successfully"
    else
        echo "   ⚠️ VoiceVox may have failed to start"
    fi
else
    echo "   ⚠️ VoiceVox run script not found at ./s_compornents/compornents/voicevox/run"
    echo "   🔊 TTS functionality may be limited"
fi

# 5. Start PiVot Assistant
echo "🎤 Starting PiVot Smart Assistant (Linux)..."

# Kill any existing processes
pkill -f "python.*main.py" 2>/dev/null || true
sleep 2

# Start main assistant process in background
python3 main.py &
MAIN_PID=$!
echo "   Assistant PID: $MAIN_PID"

# Wait a moment for startup
sleep 3

# Check if process is still running
if ! kill -0 $MAIN_PID 2>/dev/null; then
    echo "❌ PiVot Assistant failed to start"
    echo "   Check for error messages above"
    exit 1
fi

echo "================================================"
echo "✅ PiVot Smart Assistant System Started!"
echo ""
echo "🔗 Remote Services (Windows PC):"
echo "   NPU Server: http://$WINDOWS_PC_IP:8000"
echo "   Upload Server: http://$WINDOWS_PC_IP:8001"  
echo "   Swagger UI: http://$WINDOWS_PC_IP:8000/docs"
echo ""
echo "🔊 Local Services (Raspberry Pi):"
echo "   VoiceVox TTS: http://localhost:50021"
echo ""
echo "🎤 Say 'taro_two' to activate the assistant"
echo "📷 Camera will capture and send to Windows PC for NPU processing"
echo "🛑 Press Ctrl+C to stop the assistant"
echo "================================================"

# Handle cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping PiVot Assistant..."
    kill $MAIN_PID 2>/dev/null || true
    pkill -f "python.*main.py" 2>/dev/null || true
    
    # Stop VoiceVox if running
    if [ ! -z "$VOICEVOX_PID" ]; then
        echo "🔊 Stopping VoiceVox TTS Engine..."
        kill $VOICEVOX_PID 2>/dev/null || true
        pkill -f "voicevox" 2>/dev/null || true
    fi
    
    echo "✅ PiVot Assistant stopped"
    exit 0
}

trap cleanup INT TERM

# Wait for main process
wait $MAIN_PID