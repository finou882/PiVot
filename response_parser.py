"""
AI応答解析ユーティリティ

AI応答からタグを抽出・解析する共通関数を提供
"""

import re
from servo_control import cam_move, url


def extract_response_text(ai_response):
    """
    AI応答から<response>タグ内のテキストを抽出
    タグがない場合は応答全体を返す
    
    Args:
        ai_response (str): AIの生の応答
    
    Returns:
        str: 音声出力用のテキスト
    """
    # <response>...</response> の内容を抽出
    response_match = re.search(r'<response>(.*?)</response>', ai_response, re.DOTALL)
    if response_match:
        return response_match.group(1).strip()
    
    # タグがない場合は応答全体を返す（後方互換性）
    return ai_response.strip()


def extract_code_blocks(ai_response):
    """
    AI応答から<code>タグ内のコードを抽出
    
    Args:
        ai_response (str): AIの生の応答
    
    Returns:
        list: 抽出されたコードブロックのリスト
    """
    # <code>...</code> の内容をすべて抽出
    code_blocks = re.findall(r'<code>(.*?)</code>', ai_response, re.DOTALL)
    return [code.strip() for code in code_blocks]


def execute_action_code(code_string):
    """
    抽出されたコードを安全に実行
    
    Args:
        code_string (str): 実行するPythonコード
    """
    if not code_string:
        return
    
    print(f"🎯 アクション実行: {code_string}")
    
    # 安全な実行環境を構築（許可された関数のみ）
    safe_globals = {
        'cam_move': cam_move,
        'url': url,
        '__builtins__': {},  # 組み込み関数を制限
    }
    
    try:
        # コードを実行
        exec(code_string, safe_globals)
        print("✅ アクション実行完了")
    except Exception as e:
        print(f"❌ アクション実行エラー: {e}")
        print(f"   コード: {code_string}")
