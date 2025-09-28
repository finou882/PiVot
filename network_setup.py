#!/usr/bin/env python3
"""
Network Configuration Helper
Windows PC (PiVot-Server) の IP アドレスを自動検出
"""

import socket
import subprocess
import re
import requests
import asyncio
import aiohttp
from typing import Optional, List

def get_local_ip() -> str:
    """自分（Raspberry Pi）のIPアドレスを取得"""
    try:
        # ダミー接続でローカルIPを取得
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "192.168.1.0"

def get_network_range() -> str:
    """ネットワーク範囲を取得"""
    local_ip = get_local_ip()
    # IPアドレスの最後のオクテットを0に変更
    network = ".".join(local_ip.split(".")[:-1]) + ".0"
    return f"{network}/24"

def scan_network_for_pivot_server(network_range: str = None) -> Optional[str]:
    """ネットワーク内でPiVot-Serverを検索"""
    if network_range is None:
        network_range = get_network_range()
    
    print(f"🔍 Scanning network {network_range} for PiVot-Server...")
    
    # ネットワーク範囲からIPリストを生成
    base_ip = network_range.split("/")[0]
    base_octets = base_ip.split(".")[:3]
    
    # 並列でポートスキャンを実行
    async def check_ip(ip: str) -> Optional[str]:
        try:
            url = f"http://{ip}:8001/health"
            
            # 短いタイムアウトでヘルスチェック
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=3)
            ) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "npu" in data or "pivot" in str(data).lower():
                            print(f"✅ Found PiVot-Server at {ip}:8001")
                            return ip
        except:
            pass
        return None
    
    async def scan_range():
        tasks = []
        
        # IP範囲をスキャン (192.168.1.1 ~ 192.168.1.254)
        for i in range(1, 255):
            ip = ".".join(base_octets) + f".{i}"
            # 自分のIPはスキップ
            if ip != get_local_ip():
                tasks.append(check_ip(ip))
        
        # 並列実行
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 結果から有効なIPを抽出
        for result in results:
            if isinstance(result, str):
                return result
        
        return None
    
    try:
        # 非同期スキャンを実行
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(scan_range())
    except Exception as e:
        print(f"❌ Network scan error: {e}")
        return None

def detect_windows_pc_ip() -> Optional[str]:
    """Windows PC のIPアドレスを検出"""
    
    print("🔍 Detecting Windows PC (PiVot-Server)...")
    
    # 方法1: ARPテーブルから検索
    try:
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
        if result.returncode == 0:
            # Windows系のMACアドレス範囲を検索
            windows_patterns = [
                r'(\d+\.\d+\.\d+\.\d+)\s+([0-9a-f]{2}[:-][0-9a-f]{2}[:-][0-9a-f]{2}[:-][0-9a-f]{2}[:-][0-9a-f]{2}[:-][0-9a-f]{2})',
            ]
            
            for pattern in windows_patterns:
                matches = re.findall(pattern, result.stdout, re.IGNORECASE)
                for ip, mac in matches:
                    # 一般的なWindowsのベンダーMACアドレスプレフィックス
                    windows_prefixes = ['00-15-5d', '00-50-56', '08-00-27']  # Hyper-V, VMware, VirtualBox
                    if any(mac.lower().startswith(prefix.lower().replace('-', ':')) for prefix in windows_prefixes):
                        print(f"🖥️ Potential Windows PC found at {ip} (MAC: {mac})")
                        # PiVot-Serverが動いているかチェック
                        if check_pivot_server_at_ip(ip):
                            return ip
    except Exception as e:
        print(f"⚠️ ARP table scan failed: {e}")
    
    # 方法2: ネットワークスキャン
    detected_ip = scan_network_for_pivot_server()
    if detected_ip:
        return detected_ip
    
    print("❌ Windows PC (PiVot-Server) not found")
    return None

def check_pivot_server_at_ip(ip: str) -> bool:
    """指定IPでPiVot-Serverが動作しているかチェック"""
    try:
        response = requests.get(f"http://{ip}:8001/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            # PiVot-Serverの特徴的な応答をチェック
            if "npu" in str(data).lower() or "pivot" in str(data).lower():
                print(f"✅ PiVot-Server confirmed at {ip}:8001")
                return True
    except:
        pass
    return False

def update_config_file(windows_ip: str):
    """config.py を更新"""
    config_path = "config.py"
    
    try:
        with open(config_path, 'r') as f:
            content = f.read()
        
        # WINDOWS_PC_IP を更新
        updated_content = re.sub(
            r'WINDOWS_PC_IP = "[^"]*"',
            f'WINDOWS_PC_IP = "{windows_ip}"',
            content
        )
        
        with open(config_path, 'w') as f:
            f.write(updated_content)
        
        print(f"✅ config.py updated with Windows PC IP: {windows_ip}")
        
    except Exception as e:
        print(f"❌ Failed to update config.py: {e}")

def main():
    """メイン実行"""
    print("🔧 PiVot Network Configuration Helper")
    print("=" * 50)
    
    print(f"📍 Local IP (Raspberry Pi): {get_local_ip()}")
    print(f"🌐 Network Range: {get_network_range()}")
    
    # Windows PC を自動検出
    windows_ip = detect_windows_pc_ip()
    
    if windows_ip:
        print(f"\n🎯 Windows PC (PiVot-Server) found at: {windows_ip}")
        
        # 設定ファイルを更新するか確認
        response = input("📝 Update config.py with this IP? (y/N): ")
        if response.lower() == 'y':
            update_config_file(windows_ip)
        
        print(f"\n🔗 PiVot-Server URLs:")
        print(f"   NPU Server: http://{windows_ip}:8001")
        print(f"   Upload Server: http://{windows_ip}:8002")
        print(f"   Swagger UI: http://{windows_ip}:8001/docs")
        
    else:
        print("\n⚠️ Windows PC not detected automatically.")
        print("📝 Please manually configure the IP address in config.py")
        print("💡 You can find the Windows PC IP with: ipconfig (on Windows)")
    
    print("=" * 50)

if __name__ == "__main__":
    main()