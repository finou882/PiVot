import os
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

load_dotenv()

# プロキシ設定（環境変数から読み込み）
proxy_http = os.getenv('HTTP_PROXY') or os.getenv('http_proxy')
proxy_https = os.getenv('HTTPS_PROXY') or os.getenv('https_proxy')

#if proxy_http or proxy_https:
 #   print(f"プロキシを使用します: HTTP={proxy_http}, HTTPS={proxy_https}")
  #  # 環境変数が設定されていれば、requestsライブラリが自動的に使用します
   # os.environ['HTTP_PROXY'] = proxy_http or ''
    #os.environ['HTTPS_PROXY'] = proxy_https or ''

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

# gemini-flash-lite-latest モデルを使用
gemini_model = genai.GenerativeModel("gemini-flash-lite-latest")

# gemini-flash-lite-latest モデルを使用
gemini_model = genai.GenerativeModel("gemini-flash-lite-latest")

# 画像ファイルパスの設定
default_image_path = r"C:\Users\finou\OneDrive\画像\Camera Roll\WIN_20251022_23_33_40_Pro.jpg"
image_path_input = input(f"画像ファイルパスを入力してください（Enterでデフォルト使用）: ")
image_path = image_path_input.strip() if image_path_input.strip() else default_image_path

print(f"使用する画像: {image_path}")

try:
    image = Image.open(image_path)
    print("画像の読み込みが完了しました。")
except FileNotFoundError:
    print(f"画像ファイルが見つかりません: {image_path}")
    exit(1)
except Exception as e:
    print(f"画像の読み込みでエラーが発生しました: {e}")
    exit(1)

# prompt.txtから事前プロンプトを読み込み
try:
    with open("prompt.txt", "r", encoding="utf-8") as f:
        base_prompt = f.read().strip()
    print("事前プロンプト:")
    print(base_prompt)
    print("\n" + "="*50 + "\n")
except FileNotFoundError:
    base_prompt = ""
    print("prompt.txtが見つかりません。事前プロンプトなしで実行します。")

# ユーザーからの追加入力を受け取り
user_input = input("追加の質問や指示を入力してください: ")

# 事前プロンプトとユーザー入力を結合
if base_prompt:
    full_prompt = base_prompt + user_input
else:
    full_prompt = user_input

print(f"\n送信するプロンプト:\n{full_prompt}")
print("\n" + "="*50 + "\n")

# APIリクエスト実行
print("APIリクエストを送信中...")
response = gemini_model.generate_content([full_prompt, image])
print(f"\nモデル: gemini-flash-lite-latest")
print("="*60)
print("🤖 AIの回答:")
print("="*60)
print(f"{response.text}")
print("="*60)
