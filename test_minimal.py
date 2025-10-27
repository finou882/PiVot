#!/usr/bin/env python3
"""
サーボ制御とAI応答解析の最小テストスクリプト（依存関係なし）
"""

import sys
import os

# モジュールのパスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 共有ユーティリティモジュールから関数をインポート
from response_parser import extract_response_text, extract_code_blocks

def test_extract_response_text():
    """<response>タグからテキスト抽出のテスト"""
    print("=== test_extract_response_text ===")
    
    # テスト1: <response>タグあり
    ai_response1 = "<response>これはテストです。</response><code>cam_move(shaft='z', angle=90)</code>"
    result1 = extract_response_text(ai_response1)
    assert result1 == "これはテストです。", f"Expected 'これはテストです。', got '{result1}'"
    print("✅ Test 1 passed: <response>タグからテキスト抽出")
    
    # テスト2: <response>タグなし（後方互換性）
    ai_response2 = "タグなしの応答です。"
    result2 = extract_response_text(ai_response2)
    assert result2 == "タグなしの応答です。", f"Expected 'タグなしの応答です。', got '{result2}'"
    print("✅ Test 2 passed: タグなしの応答を全体として返す")
    
    # テスト3: 複数行の<response>タグ
    ai_response3 = """<response>
    これは複数行の
    テストです。
    </response>"""
    result3 = extract_response_text(ai_response3)
    assert "複数行" in result3, f"Expected multi-line text, got '{result3}'"
    print("✅ Test 3 passed: 複数行のテキスト抽出")
    
    print()

def test_extract_code_blocks():
    """<code>タグからコード抽出のテスト"""
    print("=== test_extract_code_blocks ===")
    
    # テスト1: 単一の<code>タグ
    ai_response1 = "<response>右を見ます。</response><code>cam_move(shaft='z', angle=180)</code>"
    result1 = extract_code_blocks(ai_response1)
    assert len(result1) == 1, f"Expected 1 code block, got {len(result1)}"
    assert "cam_move" in result1[0], f"Expected 'cam_move' in code, got '{result1[0]}'"
    print(f"✅ Test 1 passed: 単一コードブロック抽出: {result1[0]}")
    
    # テスト2: 複数の<code>タグ
    ai_response2 = """<response>カメラを移動します。</response>
    <code>cam_move(shaft='z', angle=90)</code>
    <code>cam_move(shaft='x', angle=180)</code>"""
    result2 = extract_code_blocks(ai_response2)
    assert len(result2) == 2, f"Expected 2 code blocks, got {len(result2)}"
    print(f"✅ Test 2 passed: 複数コードブロック抽出: {len(result2)}個")
    for i, code in enumerate(result2, 1):
        print(f"   コード {i}: {code}")
    
    # テスト3: <code>タグなし
    ai_response3 = "<response>コードはありません。</response>"
    result3 = extract_code_blocks(ai_response3)
    assert len(result3) == 0, f"Expected 0 code blocks, got {len(result3)}"
    print("✅ Test 3 passed: コードなしの場合")
    
    # テスト4: 複雑な例（RAG.txtからの実例）
    ai_response4 = "カメラヲミギニ20ド、スイヘイイドウサセマス。 <code> cam_move(shaft='z', angle=110) </code>"
    result4 = extract_code_blocks(ai_response4)
    assert len(result4) == 1, f"Expected 1 code block, got {len(result4)}"
    assert "110" in result4[0], f"Expected '110' in code, got '{result4[0]}'"
    print(f"✅ Test 4 passed: RAG.txt形式の抽出: {result4[0]}")
    
    # テスト5: RAG.txtからの複雑な実例（複数コマンド）
    ai_response5 = """<response>カメラヲヒダリシタスミヘイドウサセマス。</response> 
    <code> cam_move(shaft='z', angle=30) cam_move(shaft='x', angle=30) </code>"""
    result5 = extract_code_blocks(ai_response5)
    assert len(result5) == 1, f"Expected 1 code block, got {len(result5)}"
    assert "angle=30" in result5[0], f"Expected 'angle=30' in code, got '{result5[0]}'"
    print(f"✅ Test 5 passed: 複数関数呼び出しの抽出: {result5[0]}")
    
    print()

def test_integration():
    """統合テスト: AI応答の完全な処理"""
    print("=== test_integration ===")
    
    # RAG.txtからの実例
    sample_responses = [
        # 例1: 単純なカメラ移動
        "<response>カメラヲミギニ20ド、スイヘイイドウサセマス。</response> <code> cam_move(shaft='z', angle=110) </code>",
        
        # 例2: 複合制御
        "<response>カメラヲミギウエスミヘイドウサセマス。</response> <code> cam_move(shaft='z', angle=150) cam_move(shaft='x', angle=150) </code>",
        
        # 例3: URL表示
        '<response>GOOGLEノキューアールコードヲヒョウジシマス。</response> <code> url("https://www.google.com") </code>',
        
        # 例4: コードなし
        "<response>ソレハアオイコップデス。</response>",
    ]
    
    for i, response in enumerate(sample_responses, 1):
        print(f"\n--- テストケース {i} ---")
        print(f"AI応答: {response[:80]}...")
        
        # ステップ1: 音声テキスト抽出
        speech_text = extract_response_text(response)
        print(f"✓ 音声テキスト: {speech_text}")
        
        # ステップ2: コード抽出
        code_blocks = extract_code_blocks(response)
        print(f"✓ コードブロック数: {len(code_blocks)}")
        
        # ステップ3: コード内容表示
        if code_blocks:
            for j, code in enumerate(code_blocks, 1):
                print(f"  コード {j}: {code}")
        else:
            print("  （コードなし）")
    
    print("\n✅ Integration test passed: すべてのテストケースを処理")
    print()

def main():
    """すべてのテストを実行"""
    print("\n" + "="*60)
    print("サーボ制御とAI応答解析のテスト開始（最小バージョン）")
    print("="*60 + "\n")
    
    try:
        test_extract_response_text()
        test_extract_code_blocks()
        test_integration()
        
        print("="*60)
        print("✅ すべてのテストが成功しました！")
        print("="*60)
        return 0
    
    except AssertionError as e:
        print(f"\n❌ テスト失敗: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
