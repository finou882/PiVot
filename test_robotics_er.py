#!/usr/bin/env python3
"""
Gemini-Robotics-ER統合のテストスクリプト

このスクリプトはRobotics-ERモデルの画像解析機能をテストします。
実際のAPIキーが必要なため、環境変数GOOGLE_API_KEYを設定してください。
"""

import os
from PIL import Image
from dotenv import load_dotenv
import google.generativeai as genai

# 環境変数を読み込み
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

if not GOOGLE_API_KEY:
    print("エラー: GOOGLE_API_KEYが設定されていません。")
    print("テストをスキップします。")
    exit(0)

# APIを設定
genai.configure(api_key=GOOGLE_API_KEY)

# Robotics-ERモデルを初期化
ROBOTICS_MODEL_NAME = "gemini-2.0-flash-exp"
robotics_model = genai.GenerativeModel(ROBOTICS_MODEL_NAME)

print(f"✅ Robotics-ERモデル ({ROBOTICS_MODEL_NAME}) を初期化しました")

# テスト画像を読み込み
test_image_path = "hello.jpg"
if not os.path.exists(test_image_path):
    print(f"エラー: テスト画像 {test_image_path} が見つかりません。")
    exit(1)

image = Image.open(test_image_path)
print(f"✅ テスト画像を読み込みました: {test_image_path}")

# Robotics-ERモデルで画像を解析
print("\n🤖 Robotics-ERモデルで画像を解析中...")
try:
    prompt = "この画像に写っているものを詳しく説明してください。物体の位置、色、形状、空間的な関係性を含めて説明してください。"
    response = robotics_model.generate_content([prompt, image])
    analysis_result = response.text
    
    print(f"\n🔍 Robotics-ER解析結果:")
    print("=" * 80)
    print(analysis_result)
    print("=" * 80)
    
    print("\n✅ テスト成功: Robotics-ERモデルが正常に動作しました")
    
except Exception as e:
    print(f"\n❌ テスト失敗: {e}")
    exit(1)

print("\n📝 次のステップ:")
print("1. main.pyでRobotics-ER解析がプロンプトに統合されることを確認")
print("2. 実際のロボットでカメラ撮影→Robotics-ER解析→Gemini応答のフローをテスト")
