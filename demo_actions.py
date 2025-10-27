#!/usr/bin/env python3
"""
AI応答解析のデモスクリプト
実際のAI応答を模擬して、解析と実行の流れを確認します
"""

import sys
import os

# モジュールのパスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 共有ユーティリティモジュールから関数をインポート
from response_parser import extract_response_text, extract_code_blocks, execute_action_code

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
