#!/usr/bin/env python3
"""
サーボ制御とAI応答統合のテストスクリプト
"""

import sys
import re

# 相対インポート
try:
    from servo_control import cam_move, url
except ImportError:
    print("Error: servo_control.pyをインポートできません")
    sys.exit(1)


def parse_ai_response(response_text):
    """
    AI応答からタグを抽出して分離する（main.pyからコピー）
    """
    result = {
        'response': '',
        'code': '',
        'raw': response_text
    }
    
    # <response>タグの抽出
    response_match = re.search(r'<response>(.*?)</response>', response_text, re.DOTALL)
    if response_match:
        result['response'] = response_match.group(1).strip()
    
    # <code>タグの抽出
    code_match = re.search(r'<code>(.*?)</code>', response_text, re.DOTALL)
    if code_match:
        result['code'] = code_match.group(1).strip()
    
    # タグを除去した全文を取得
    raw_text = response_text
    raw_text = re.sub(r'<response>.*?</response>', '', raw_text, flags=re.DOTALL)
    raw_text = re.sub(r'<code>.*?</code>', '', raw_text, flags=re.DOTALL)
    result['raw'] = raw_text.strip()
    
    return result


def execute_ai_code(code_string):
    """
    AI応答から抽出したコードを安全に実行する（main.pyからコピー）
    """
    if not code_string:
        return True
    
    print(f"🔧 コード実行: {code_string}")
    
    # 安全な実行環境を準備
    allowed_globals = {
        'cam_move': cam_move,
        'url': url,
        '__builtins__': {}
    }
    
    try:
        exec(code_string, allowed_globals, {})
        print("✅ コード実行完了")
        return True
    except Exception as e:
        print(f"❌ コード実行エラー: {e}")
        return False


def test_response_parsing():
    """応答パーステストケース"""
    print("\n=== テスト1: 応答パース ===")
    
    # テストケース1: <response>と<code>の両方がある場合
    test1 = """<response>カメラをミギニ20ド、スイヘイイドウサセマス。</response> <code>cam_move(shaft='z', angle=110)</code>"""
    result1 = parse_ai_response(test1)
    assert result1['response'] == "カメラをミギニ20ド、スイヘイイドウサセマス。"
    assert result1['code'] == "cam_move(shaft='z', angle=110)"
    print(f"✅ テスト1合格: {result1}")
    
    # テストケース2: <response>のみの場合
    test2 = """<response>ソレハアオイコップデス。</response>"""
    result2 = parse_ai_response(test2)
    assert result2['response'] == "ソレハアオイコップデス。"
    assert result2['code'] == ""
    print(f"✅ テスト2合格: {result2}")
    
    # テストケース3: <code>のみの場合
    test3 = """カメラヲショウメンヘモドシマス。 <code>cam_move(shaft='z', angle=90)</code>"""
    result3 = parse_ai_response(test3)
    assert result3['code'] == "cam_move(shaft='z', angle=90)"
    print(f"✅ テスト3合格: {result3}")
    
    # テストケース4: 複数行のコード
    test4 = """<response>右上隅を見ます。</response> <code>cam_move(shaft='z', angle=150)
cam_move(shaft='x', angle=150)</code>"""
    result4 = parse_ai_response(test4)
    assert "cam_move(shaft='z', angle=150)" in result4['code']
    assert "cam_move(shaft='x', angle=150)" in result4['code']
    print(f"✅ テスト4合格: {result4}")
    
    print("✅ すべての応答パーステストに合格しました！\n")


def test_code_execution():
    """コード実行テストケース"""
    print("\n=== テスト2: コード実行 ===")
    
    # テストケース1: 単一のcam_move
    code1 = "cam_move('z', 90)"
    result1 = execute_ai_code(code1)
    assert result1 == True
    print(f"✅ テスト1合格")
    
    # テストケース2: 複数のcam_move
    code2 = """cam_move('z', 150)
cam_move('x', 150)"""
    result2 = execute_ai_code(code2)
    assert result2 == True
    print(f"✅ テスト2合格")
    
    # テストケース3: url関数
    code3 = 'url("https://www.google.com")'
    result3 = execute_ai_code(code3)
    assert result3 == True
    print(f"✅ テスト3合格")
    
    # テストケース4: 不正なコード（セキュリティテスト）
    code4 = "import os; os.system('ls')"
    result4 = execute_ai_code(code4)
    # 実行に失敗するはず（osモジュールが使えない）
    assert result4 == False
    print(f"✅ テスト4合格（不正コードが正しくブロックされました）")
    
    print("✅ すべてのコード実行テストに合格しました！\n")


def test_full_integration():
    """統合テストケース"""
    print("\n=== テスト3: 統合テスト ===")
    
    # RAG.txtの例に基づいたテストケース
    test_responses = [
        # Z軸制御
        """<response>カメラヲミギニ20ド、スイヘイイドウサセマス。</response> <code>cam_move(shaft='z', angle=110)</code>""",
        # X軸制御
        """<response>カメラヲショウメンノキジュンイチカラウエヘ10ドケイシャサセマス。</response> <code>cam_move(shaft='x', angle=170)</code>""",
        # 複合制御
        """<response>カメラヲミギウエスミヘイドウサセマス。</response> <code>cam_move(shaft='z', angle=150)
cam_move(shaft='x', angle=150)</code>""",
        # URL表示
        """<response>GOOGLEノキューアールコードヲヒョウジシマス。</response> <code>url("https://www.google.com")</code>""",
    ]
    
    for i, response in enumerate(test_responses, 1):
        print(f"\n--- 統合テスト {i} ---")
        parsed = parse_ai_response(response)
        print(f"応答テキスト: {parsed['response']}")
        print(f"実行コード: {parsed['code']}")
        
        if parsed['code']:
            success = execute_ai_code(parsed['code'])
            assert success == True
        
        print(f"✅ 統合テスト {i} 合格")
    
    print("\n✅ すべての統合テストに合格しました！\n")


if __name__ == "__main__":
    print("=== PiVot サーボ統合テスト開始 ===\n")
    
    try:
        test_response_parsing()
        test_code_execution()
        test_full_integration()
        
        print("\n" + "="*50)
        print("🎉 すべてのテストに合格しました！")
        print("="*50)
        
    except AssertionError as e:
        print(f"\n❌ テスト失敗: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
