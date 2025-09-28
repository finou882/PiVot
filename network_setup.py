#!/usr/bin/env python3
"""
PiVot Network Configuration Helper
Automatically detects Windows PC running PiVot-Server and configures connection
"""

import socket
import subprocess
import ipaddress
import asyncio
import aiohttp
import json
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict

class NetworkConfigHelper:
    def __init__(self):
        self.local_ip = self.get_local_ip()
        self.network_range = self.get_network_range()
        self.config_file = "config.py"
        
    def get_local_ip(self) -> str:
        """Get the local IP address of this device"""
        try:
            # Connect to a remote address to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"
    
    def get_network_range(self) -> str:
        """Get the network range (e.g., 192.168.1.0/24)"""
        try:
            ip = ipaddress.IPv4Address(self.local_ip)
            # Assume /24 subnet
            network = ipaddress.IPv4Network(f"{ip}/24", strict=False)
            return str(network)
        except Exception:
            return "192.168.1.0/24"
    
    def get_arp_table(self) -> List[Dict[str, str]]:
        """Get ARP table entries using multiple methods"""
        arp_entries = []
        
        # Method 1: Try /proc/net/arp (Linux)
        try:
            with open('/proc/net/arp', 'r') as f:
                lines = f.readlines()[1:]  # Skip header
                for line in lines:
                    parts = line.strip().split()
                    if len(parts) >= 6 and parts[3] != "00:00:00:00:00:00":
                        arp_entries.append({
                            'ip': parts[0],
                            'mac': parts[3],
                            'interface': parts[5]
                        })
        except FileNotFoundError:
            pass
        
        # Method 2: Try ip neigh (modern Linux)
        try:
            result = subprocess.run(['ip', 'neigh'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'REACHABLE' in line or 'STALE' in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            ip = parts[0]
                            mac = next((p for p in parts if ':' in p and len(p) == 17), None)
                            if mac:
                                arp_entries.append({
                                    'ip': ip,
                                    'mac': mac,
                                    'interface': 'unknown'
                                })
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Method 3: Try arp command if available
        try:
            result = subprocess.run(['arp', '-a'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if '(' in line and ')' in line:
                        try:
                            ip = line.split('(')[1].split(')')[0]
                            if 'at' in line:
                                mac = line.split('at ')[1].split(' ')[0]
                                arp_entries.append({
                                    'ip': ip,
                                    'mac': mac,
                                    'interface': 'unknown'
                                })
                        except (IndexError, ValueError):
                            continue
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        return arp_entries
    
    async def check_pivot_server(self, session: aiohttp.ClientSession, ip: str) -> bool:
        """Check if PiVot-Server is running on the given IP"""
        urls_to_try = [
            f"http://{ip}:8000/health",
            f"http://{ip}:8000/",
            f"http://{ip}:8001/health",
            f"http://{ip}:8001/"
        ]
        
        for url in urls_to_try:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=2)) as response:
                    if response.status == 200:
                        text = await response.text()
                        # Check for PiVot-Server indicators
                        if any(keyword in text.lower() for keyword in 
                              ['pivot', 'npu', 'voice', 'assistant', 'server']):
                            return True
            except (aiohttp.ClientError, asyncio.TimeoutError):
                continue
        
        return False
    
    async def scan_network_for_pivot_server(self) -> Optional[str]:
        """Scan the network for PiVot-Server"""
        print(f"🔍 Scanning network {self.network_range} for PiVot-Server...")
        
        # Get network hosts to scan
        network = ipaddress.IPv4Network(self.network_range)
        hosts_to_scan = []
        
        # First, try ARP table entries
        arp_entries = self.get_arp_table()
        if arp_entries:
            print(f"📋 Found {len(arp_entries)} devices in ARP table")
            hosts_to_scan.extend([entry['ip'] for entry in arp_entries])
        else:
            print("⚠️ No ARP entries found, scanning common IP ranges...")
            # Fallback: scan common IP ranges
            local_ip = ipaddress.IPv4Address(self.local_ip)
            base_ip = str(local_ip).rsplit('.', 1)[0]
            
            # Scan common host IPs first
            common_ips = [f"{base_ip}.{i}" for i in [1, 2, 10, 100, 101, 110, 120, 200, 254]]
            hosts_to_scan.extend(common_ips)
        
        # Remove duplicates and local IP
        hosts_to_scan = list(set(hosts_to_scan))
        if self.local_ip in hosts_to_scan:
            hosts_to_scan.remove(self.local_ip)
        
        # Scan hosts
        connector = aiohttp.TCPConnector(limit=10)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [self.check_pivot_server(session, ip) for ip in hosts_to_scan[:20]]  # Limit to first 20
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if result is True:
                    return hosts_to_scan[i]
        
        return None
    
    def create_or_update_config(self, windows_ip: str) -> bool:
        """Create or update config.py with Windows PC IP"""
        
        # Check if config.py already exists
        if os.path.exists(self.config_file):
            # Update existing config file
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Update the Windows PC IP line
                import re
                pattern = r'WINDOWS_PC_IP\s*=\s*["\'][^"\']*["\']'
                replacement = f'WINDOWS_PC_IP = "{windows_ip}"'
                
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                else:
                    # Add the IP configuration if not found
                    content = content.replace(
                        '# Network Configuration (ネットワーク設定)',
                        f'# Network Configuration (ネットワーク設定)\nWINDOWS_PC_IP = "{windows_ip}"'
                    )
                
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✅ Updated existing config.py with IP: {windows_ip}")
                return True
                
            except Exception as e:
                print(f"⚠️ Failed to update existing config: {e}")
                # Fall back to creating new config
        
        # Create new config file if update failed or file doesn't exist
        config_content = f'''# PiVot Smart Assistant Configuration
# Auto-updated by network_setup.py
# Generated: {os.popen("date").read().strip()}

# ===========================================
# Network Configuration (ネットワーク設定)
# ===========================================

# Windows PC (PiVot-Server) の IP アドレス - Auto-detected
WINDOWS_PC_IP = "{windows_ip}"

# PiVot-Server (Windows) 設定
PIVOT_SERVER_URL = f"http://{{WINDOWS_PC_IP}}:8000"
IMAGE_UPLOAD_SERVER_URL = f"http://{{WINDOWS_PC_IP}}:8001"

# Raspberry Pi Configuration  
RASPBERRY_PI_IP = "{self.local_ip}"

# ===========================================
# Raspberry Pi (PiVot) 設定
# ===========================================

# Raspberry Pi Camera 設定
CAMERA_RESOLUTION = (1920, 1080)  # カメラ解像度
CAMERA_MOCK_MODE = False  # True = テストモード, False = 実際のカメラ使用

# ウェイクワード設定
WAKEWORD_MODEL_PATH = "s_compornents/compornents/taro_tsuu.onnx"
WAKEWORD_THRESHOLD = 0.01  # 検出感度 (低いほど敏感)
WAKEWORD_COOLDOWN = 2.0  # 連続検出防止時間(秒)

# 音声設定
AUDIO_INPUT_DEVICE_INDEX = 2  # マイクデバイス番号 (rr.py で確認)
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1

# Voice Assistant Settings
VOICE_ASSISTANT_NAME = "タロー通"
RESPONSE_MAX_LENGTH = 100

print(f"🔧 PiVot Configuration loaded:")
print(f"   Windows PC: {{WINDOWS_PC_IP}}")
print(f"   Raspberry Pi: {{RASPBERRY_PI_IP if 'RASPBERRY_PI_IP' in globals() else 'Auto-detected'}}")
print(f"   Server URL: {{PIVOT_SERVER_URL}}")
'''
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write(config_content)
            print(f"✅ Created new config.py with IP: {windows_ip}")
            return True
        except Exception as e:
            print(f"❌ Failed to write config: {e}")
            return False
    
    def test_connection(self, windows_ip: str) -> bool:
        """Test connection to Windows PC"""
        test_urls = [
            f"http://{windows_ip}:8000/health",
            f"http://{windows_ip}:8000/",
            f"http://{windows_ip}:8001/health",
            f"http://{windows_ip}:8001/"
        ]
        
        for url in test_urls:
            try:
                import requests
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ Connection test successful: {url}")
                    return True
            except Exception as e:
                continue
        
        print(f"⚠️ Connection test failed for {windows_ip}")
        print("   Make sure PiVot-Server is running on Windows PC")
        print("   Check Windows firewall allows connections on port 8000/8001")
        return False
    
    def get_manual_ip(self) -> Optional[str]:
        """Get IP address manually from user"""
        print("\n" + "="*50)
        print("🔧 Manual Configuration Required")
        print("="*50)
        print(f"Current network: {self.network_range}")
        print(f"Raspberry Pi IP: {self.local_ip}")
        print()
        print("To find your Windows PC IP address:")
        print("  1. Open Command Prompt on Windows")
        print("  2. Run: ipconfig")
        print("  3. Look for 'IPv4 Address' under your network adapter")
        print()
        
        try:
            ip = input("Enter Windows PC IP address (or press Enter to skip): ").strip()
            if not ip:
                return None
            
            # Validate IP
            ipaddress.IPv4Address(ip)
            return ip
            
        except (ValueError, KeyboardInterrupt):
            return None

async def main():
    print("🔧 PiVot Network Configuration Helper")
    print("="*50)
    
    helper = NetworkConfigHelper()
    
    print(f"📍 Local IP (Raspberry Pi): {helper.local_ip}")
    print(f"🌐 Network Range: {helper.network_range}")
    print("🔍 Detecting Windows PC (PiVot-Server)...")
    
    # Try automatic detection
    windows_ip = await helper.scan_network_for_pivot_server()
    
    if windows_ip:
        print(f"✅ Found PiVot-Server at: {windows_ip}")
        
        # Create config file
        if helper.create_or_update_config(windows_ip):
            print(f"✅ Configuration saved to: {helper.config_file}")
            
            # Test connection
            if helper.test_connection(windows_ip):
                print("🎉 Network configuration complete!")
            else:
                print("⚠️ Configuration saved, but connection test failed")
        else:
            print("❌ Failed to save configuration")
    else:
        print("❌ Windows PC (PiVot-Server) not found")
        
        # Try manual configuration
        manual_ip = helper.get_manual_ip()
        if manual_ip:
            if helper.create_or_update_config(manual_ip):
                print(f"✅ Manual configuration saved: {manual_ip}")
                helper.test_connection(manual_ip)
            else:
                print("❌ Failed to save manual configuration")
        else:
            print("\n⚠️ Windows PC not configured automatically.")
            print("📝 Please manually configure the IP address in config.py")
            print("💡 You can find the Windows PC IP with: ipconfig (on Windows)")
    
    print("="*50)

if __name__ == "__main__":
    try:
        # Use modern asyncio syntax to avoid deprecation warning
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        print("📝 Please manually configure config.py")
        print("💡 Set WINDOWS_PC_IP to your Windows PC's IP address")