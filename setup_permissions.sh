#!/bin/bash
# Make all PiVot scripts executable

echo "🔧 Setting up script permissions..."

chmod +x start_pivot_assistant.sh
chmod +x fix_pyaudio.sh  
chmod +x network_setup.py
chmod +x test_connection.py
chmod +x check_audio.py

echo "✅ All scripts are now executable"

echo ""
echo "📋 Available scripts:"
echo "   ./start_pivot_assistant.sh - Main startup script"
echo "   ./fix_pyaudio.sh - Fix PyAudio issues"
echo "   ./check_audio.py - Diagnose audio problems" 
echo "   ./test_connection.py - Test Windows PC connection"
echo "   ./network_setup.py - Configure network settings"
echo ""
echo "🚀 To start PiVot: ./start_pivot_assistant.sh"