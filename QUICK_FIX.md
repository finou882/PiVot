# PiVot Audio Issues - Quick Fix Guide

## 🔧 Your Current Issues

1. **PyAudio GLIBCXX Error** - Conda/system library conflict
2. **Network Template Variables** - Config not properly updated  
3. **Deprecated Asyncio Warning** - Old network setup code

## 🚀 Quick Fixes (Run on Raspberry Pi)

### Fix 1: Audio Issues
```bash
# Diagnose the problem
python3 check_audio.py

# Try automatic fix
bash fix_pyaudio.sh

# Or use system Python (recommended)
conda deactivate
/usr/bin/python3 main.py
```

### Fix 2: Network Configuration
```bash
# Update IP address in config.py
nano config.py
# Change WINDOWS_PC_IP to "192.168.68.50"

# Test connection
python3 test_connection.py
```

### Fix 3: Complete Restart
```bash
# Use the fixed startup script
./start_pivot_assistant.sh
```

## 💡 Recommended Solution

The easiest fix is to use system Python instead of conda for audio:

```bash
# Install system PyAudio
sudo apt install -y python3-pyaudio portaudio19-dev

# Deactivate conda
conda deactivate

# Run with system Python
/usr/bin/python3 main.py
```

Or use the helper script:
```bash
./run_system_python.sh
```

## 📋 Files Updated

- ✅ `config.py` - Fixed IP address (192.168.68.50)
- ✅ `start_pivot_assistant.sh` - Improved startup script  
- ✅ `fix_pyaudio.sh` - Audio installation fixer
- ✅ `check_audio.py` - Audio environment checker
- ✅ `test_connection.py` - Network connectivity tester
- ✅ `run_system_python.sh` - System Python runner (auto-created)

## 🎯 Next Steps

1. **Run audio check**: `python3 check_audio.py`
2. **Fix audio**: `bash fix_pyaudio.sh` 
3. **Test connection**: `python3 test_connection.py`
4. **Start PiVot**: `./start_pivot_assistant.sh`

The conda GLIBCXX issue is common on Raspberry Pi. Using system Python for audio components is the most reliable solution.