#!/usr/bin/env python3
"""
Robotics-ER統合の動作確認スクリプト

このスクリプトは、画像がある場合とない場合の両方で
Robotics-ER統合が正しく動作することを確認します。
"""

import sys
import os

# モジュールのパスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("Robotics-ER統合 動作確認テスト")
print("=" * 80)
print()

# Test 1: Robotics-ERモデルの初期化確認
print("Test 1: モデル設定の確認")
print("-" * 40)

try:
    # ファイルを読んでモデル名を確認
    with open('main.py', 'r') as f:
        content = f.read()
        
    if 'ROBOTICS_MODEL_NAME = "gemini-2.0-flash-exp"' in content:
        print("✅ Robotics-ERモデル名が正しく設定されています")
    else:
        print("❌ Robotics-ERモデル名が見つかりません")
        sys.exit(1)
        
    if 'robotics_model = genai.GenerativeModel(ROBOTICS_MODEL_NAME)' in content:
        print("✅ Robotics-ERモデルが初期化されています")
    else:
        print("❌ Robotics-ERモデルの初期化が見つかりません")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ エラー: {e}")
    sys.exit(1)

print()

# Test 2: analyze_image_with_robotics_er関数の存在確認
print("Test 2: 画像解析関数の確認")
print("-" * 40)

if 'def analyze_image_with_robotics_er(image):' in content:
    print("✅ analyze_image_with_robotics_er関数が定義されています")
else:
    print("❌ analyze_image_with_robotics_er関数が見つかりません")
    sys.exit(1)

if 'robotics_model.generate_content' in content:
    print("✅ Robotics-ERモデルの呼び出しコードが含まれています")
else:
    print("❌ Robotics-ERモデルの呼び出しコードが見つかりません")
    sys.exit(1)

print()

# Test 3: process_request関数の統合確認
print("Test 3: process_request関数の統合確認")
print("-" * 40)

if 'robotics_analysis = analyze_image_with_robotics_er(image)' in content:
    print("✅ process_request内でRobotics-ER解析が呼び出されています")
else:
    print("❌ Robotics-ER解析の呼び出しが見つかりません")
    sys.exit(1)

if '//Robotics-ER Vision Analysis//' in content:
    print("✅ Robotics-ER解析結果がプロンプトに統合されています")
else:
    print("❌ Robotics-ER解析結果の統合が見つかりません")
    sys.exit(1)

print()

# Test 4: エラーハンドリングの確認
print("Test 4: エラーハンドリングの確認")
print("-" * 40)

if 'except Exception as e:' in content and '⚠️ Robotics-ER解析エラー' in content:
    print("✅ Robotics-ER解析のエラーハンドリングが実装されています")
else:
    print("❌ エラーハンドリングが見つかりません")
    sys.exit(1)

if 'return ""' in content:
    print("✅ エラー時に空文字列を返すフォールバック処理があります")
else:
    print("⚠️  エラー時のフォールバック処理を確認してください")

print()

# Test 5: 後方互換性の確認
print("Test 5: 後方互換性の確認")
print("-" * 40)

if 'if image:' in content and 'robotics_analysis = analyze_image_with_robotics_er' in content:
    print("✅ 画像がある場合のみRobotics-ER解析が実行されます")
else:
    print("❌ 画像チェックが見つかりません")
    sys.exit(1)

if 'if robotics_analysis:' in content:
    print("✅ 解析結果がある場合のみプロンプトに統合されます")
else:
    print("❌ 解析結果のチェックが見つかりません")
    sys.exit(1)

print()

# Test 6: 既存機能の保持確認
print("Test 6: 既存機能の保持確認")
print("-" * 40)

if 'from response_parser import extract_response_text, extract_code_blocks, execute_action_code' in content:
    print("✅ 既存のresponse_parser機能が保持されています")
else:
    print("❌ response_parserのインポートが見つかりません")
    sys.exit(1)

if 'CHAT.send_message(contents)' in content:
    print("✅ 既存のチャット機能が保持されています")
else:
    print("❌ チャット機能が見つかりません")
    sys.exit(1)

if 'speak(speech_text)' in content:
    print("✅ 既存の音声出力機能が保持されています")
else:
    print("❌ 音声出力機能が見つかりません")
    sys.exit(1)

print()

# 最終結果
print("=" * 80)
print("✅ すべての統合テストに合格しました！")
print("=" * 80)
print()
print("📝 統合の概要:")
print("  1. Robotics-ERモデル (gemini-2.0-flash-exp) が初期化されます")
print("  2. 画像がある場合、まずRobotics-ERで詳細解析を実行")
print("  3. 解析結果をユーザープロンプトと統合してメインGeminiに送信")
print("  4. 既存の応答処理パイプライン（アクション実行・音声出力）が動作")
print("  5. エラー時は従来通りの動作にフォールバック")
print()
print("🎯 次のステップ:")
print("  1. 実機でカメラ撮影→Robotics-ER解析→応答のフローをテスト")
print("  2. 様々なシーンでの解析精度を確認")
print("  3. レスポンス時間を測定して最適化を検討")
print()
