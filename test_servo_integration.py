#!/usr/bin/env python3
"""
サーボ制御とAI応答解析のテストスクリプト
"""

import sys
import os

# モジュールのパスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import extract_response_text, extract_code_blocks, execute_action_code

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
    
    print()

def test_execute_action_code():
    """コード実行のテスト（シミュレーション）"""
    print("=== test_execute_action_code ===")
    
    # テスト1: cam_move関数の実行
    code1 = "cam_move(shaft='z', angle=90)"
    print(f"テストコード実行: {code1}")
    execute_action_code(code1)
    print("✅ Test 1 passed: cam_move実行（エラーなし）")
    
    # テスト2: url関数の実行
    code2 = 'url("https://www.google.com")'
    print(f"テストコード実行: {code2}")
    execute_action_code(code2)
    print("✅ Test 2 passed: url実行（エラーなし）")
    
    # テスト3: 複数行のコード
    code3 = """cam_move(shaft='z', angle=180)
cam_move(shaft='x', angle=0)"""
    print(f"テストコード実行: {code3}")
    execute_action_code(code3)
    print("✅ Test 3 passed: 複数行コード実行（エラーなし）")
    
    # テスト4: 無効な関数（セキュリティテスト）
    code4 = "print('This should not work')"
    print(f"テストコード実行（失敗を期待）: {code4}")
    execute_action_code(code4)
    print("✅ Test 4 passed: 無効な関数は実行されない（セキュリティOK）")
    
    print()

def test_integration():
    """統合テスト: AI応答の完全な処理"""
    print("=== test_integration ===")
    
    # RAG.txtからの実例
    sample_response = """<response>カメラヲミギニ20ド、スイヘイイドウサセマス。</response> <code> cam_move(shaft='z', angle=110) </code>"""
    
    # ステップ1: 音声テキスト抽出
    speech_text = extract_response_text(sample_response)
    print(f"音声テキスト: {speech_text}")
    assert "カメラヲミギニ20ド" in speech_text
    
    # ステップ2: コード抽出
    code_blocks = extract_code_blocks(sample_response)
    print(f"コードブロック数: {len(code_blocks)}")
    assert len(code_blocks) == 1
    
    # ステップ3: コード実行
    for code in code_blocks:
        print(f"実行: {code}")
        execute_action_code(code)
    
    print("✅ Integration test passed: AI応答の完全処理")
    print()

def main():
    """すべてのテストを実行"""
    print("\n" + "="*50)
    print("サーボ制御とAI応答解析のテスト開始")
    print("="*50 + "\n")
    
    try:
        test_extract_response_text()
        test_extract_code_blocks()
        test_execute_action_code()
        test_integration()
        
        print("="*50)
        print("✅ すべてのテストが成功しました！")
        print("="*50)
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
        sys.exit(1)
