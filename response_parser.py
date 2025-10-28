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
        str: 音声出力用のテキスト（タグ自体は除外）
    """
    # <respose>...</respose> の内容のみを抽出（スペルミス版）
    respose_match = re.search(r'<respose>(.*?)</respose>', ai_response, re.DOTALL)
    if respose_match:
        content = respose_match.group(1).strip()
        print(f"🏷️ <respose>タグから抽出されたテキスト: {content}")
        return content
    
    # <response>...</response> の内容のみを抽出（正しいスペル版）
    response_match = re.search(r'<response>(.*?)</response>', ai_response, re.DOTALL)
    if response_match:
        content = response_match.group(1).strip()
        print(f"🏷️ <response>タグから抽出されたテキスト: {content}")
        return content
    
    # タグがない場合は応答全体を返す（後方互換性）
    clean_text = ai_response.strip()
    print(f"🏷️ タグなしテキスト: {clean_text}")
    return clean_text


def extract_code_blocks(ai_response):
    """
    AI応答から<code>タグ内のコードを抽出
    
    Args:
        ai_response (str): AIの生の応答
    
    Returns:
        list: 抽出されたコードブロックのリスト
    """
    print(f"🔍 コードブロック抽出開始...")
    print(f"🔍 AI応答全体: {ai_response}")
    
    # <code>...</code> の内容をすべて抽出
    code_blocks = re.findall(r'<code>(.*?)</code>', ai_response, re.DOTALL)
    
    print(f"🔍 抽出されたコードブロック数: {len(code_blocks)}")
    for i, code in enumerate(code_blocks, 1):
        print(f"🔍 ブロック {i}: {code.strip()}")
    
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
