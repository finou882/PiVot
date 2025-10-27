#!/usr/bin/env python3
"""
AI応答解析のデモスクリプト
実際のAI応答を模擬して、解析と実行の流れを確認します
"""

import sys
import os
import re

# モジュールのパスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# servo_controlから関数をインポート
from servo_control import cam_move, url

def extract_response_text(ai_response):
    """AI応答から<response>タグ内のテキストを抽出"""
    response_match = re.search(r'<response>(.*?)</response>', ai_response, re.DOTALL)
    if response_match:
        return response_match.group(1).strip()
    return ai_response.strip()

def extract_code_blocks(ai_response):
    """AI応答から<code>タグ内のコードを抽出"""
    code_blocks = re.findall(r'<code>(.*?)</code>', ai_response, re.DOTALL)
    return [code.strip() for code in code_blocks]

def execute_action_code(code_string):
    """抽出されたコードを安全に実行"""
    if not code_string:
        return
    
    print(f"🎯 アクション実行: {code_string}")
    
    safe_globals = {
        'cam_move': cam_move,
        'url': url,
        '__builtins__': {},
    }
    
    try:
        exec(code_string, safe_globals)
        print("✅ アクション実行完了\n")
    except Exception as e:
        print(f"❌ アクション実行エラー: {e}\n")

def demo_ai_responses():
    """AI応答のデモンストレーション"""
    
    print("="*70)
    print("AI応答とアクションのリンク - デモンストレーション")
    print("="*70)
    print()
    
    # デモ応答のリスト（RAG.txtから抜粋）
    demo_responses = [
        {
            "description": "1. 単純なカメラ移動（右へ20度）",
            "response": "<response>カメラを右に20度、水平移動させます。</response> <code> cam_move(shaft='z', angle=110) </code>"
        },
        {
            "description": "2. 複合制御（右上隅を見る）",
            "response": "<response>カメラを右上隅へ移動させます。</response> <code> cam_move(shaft='z', angle=150) \ncam_move(shaft='x', angle=150) </code>"
        },
        {
            "description": "3. URL QRコード表示",
            "response": '<response>GoogleのQRコードを表示します。</response> <code> url("https://www.google.com") </code>'
        },
        {
            "description": "4. 情報提供のみ（アクションなし）",
            "response": "<response>それは青いコップです。</response>"
        },
        {
            "description": "5. 全方位スキャン",
            "response": """<response>周りを下から上まですべて見渡します。</response> 
            <code> cam_move(shaft='z', angle=180) </code>
            <code> cam_move(shaft='z', angle=0) </code>
            <code> cam_move(shaft='x', angle=180) </code>
            <code> cam_move(shaft='x', angle=0) </code>"""
        }
    ]
    
    for i, demo in enumerate(demo_responses, 1):
        print(f"\n{'─'*70}")
        print(f"デモ {i}: {demo['description']}")
        print(f"{'─'*70}")
        
        ai_response = demo['response']
        print(f"📥 AI応答（生）:")
        print(f"   {ai_response[:100]}{'...' if len(ai_response) > 100 else ''}")
        print()
        
        # 音声テキストを抽出
        speech_text = extract_response_text(ai_response)
        print(f"🗣️  音声出力:")
        print(f"   {speech_text}")
        print()
        
        # コードブロックを抽出
        code_blocks = extract_code_blocks(ai_response)
        
        if code_blocks:
            print(f"📝 アクションコード: {len(code_blocks)}個のコードブロックを検出")
            for j, code in enumerate(code_blocks, 1):
                print(f"\n   [{j}] {code}")
                # コードを実行
                execute_action_code(code)
        else:
            print("📝 アクションコード: なし")
            print()
        
        # 次のデモに進む前に少し待つ
        if i < len(demo_responses):
            input("Enterキーを押して次のデモへ...")
    
    print("\n" + "="*70)
    print("デモンストレーション完了")
    print("="*70)

def main():
    """メイン関数"""
    try:
        demo_ai_responses()
        return 0
    except KeyboardInterrupt:
        print("\n\n中断されました。")
        return 0
    except Exception as e:
        print(f"\nエラー: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
