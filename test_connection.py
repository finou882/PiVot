#!/usr/bin/env python3
"""
Quick Network Connection Test
Tests connection to Windows PC PiVot-Server
"""

import sys
import os
import requests
import socket

def test_ip_connectivity(ip: str) -> bool:
    """Test basic IP connectivity"""
    try:
        # Test if IP is reachable
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((ip, 8000))
        sock.close()
        return result == 0
    except Exception:
        return False

def test_pivot_server(ip: str) -> dict:
    """Test PiVot-Server endpoints"""
    results = {
        'ip_reachable': False,
        'port_8000': False,
        'port_8001': False,
        'health_check': False,
        'server_response': None
    }
    
    # Test IP reachability
    results['ip_reachable'] = test_ip_connectivity(ip)
    
    # Test different ports and endpoints
    test_urls = [
        (f"http://{ip}:8000/health", 'port_8000', 'health_check'),
        (f"http://{ip}:8000/", 'port_8000', None),
        (f"http://{ip}:8001/health", 'port_8001', None),
        (f"http://{ip}:8001/", 'port_8001', None)
    ]
    
    for url, port_key, health_key in test_urls:
        try:
            response = requests.get(url, timeout=3)
            results[port_key] = True
            if health_key and response.status_code == 200:
                results[health_key] = True
                results['server_response'] = response.text[:200]  # First 200 chars
        except requests.exceptions.RequestException:
            continue
    
    return results

def main():
    print("🧪 PiVot Network Connection Test")
    print("=" * 40)
    
    # Try to load config
    try:
        if os.path.exists('config.py'):
            sys.path.insert(0, '.')
            import config
            windows_ip = config.WINDOWS_PC_IP
            print(f"📋 Using IP from config.py: {windows_ip}")
        else:
            windows_ip = input("Enter Windows PC IP address: ").strip()
            if not windows_ip:
                print("❌ No IP address provided")
                return
    except Exception as e:
        print(f"⚠️ Could not load config.py: {e}")
        windows_ip = input("Enter Windows PC IP address: ").strip()
        if not windows_ip:
            return
    
    print(f"\n🔍 Testing connection to {windows_ip}...")
    
    # Run tests
    results = test_pivot_server(windows_ip)
    
    # Display results
    print(f"\n📊 Test Results:")
    print(f"   IP Reachable: {'✅' if results['ip_reachable'] else '❌'}")
    print(f"   Port 8000: {'✅' if results['port_8000'] else '❌'}")
    print(f"   Port 8001: {'✅' if results['port_8001'] else '❌'}")
    print(f"   Health Check: {'✅' if results['health_check'] else '❌'}")
    
    if results['server_response']:
        print(f"\n📝 Server Response Preview:")
        print(f"   {results['server_response']}")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    if not results['ip_reachable']:
        print("   ❌ IP not reachable - check network connection")
        print("   💡 Try: ping", windows_ip)
    elif not results['port_8000'] and not results['port_8001']:
        print("   ❌ No services responding - start PiVot-Server on Windows")
        print("   💡 Run: python main_npu.py (on Windows PC)")
    elif not results['health_check']:
        print("   ⚠️ Service running but health check failed")
        print("   💡 Check if PiVot-Server is properly configured")
    else:
        print("   ✅ Connection looks good! PiVot should work.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Test cancelled")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")