import os
import subprocess
import time
import numpy as np

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from PIL import Image

# --- 音声処理ライブラリ ---
import pyaudio
from faster_whisper import WhisperModel
import wave

# --- カメラライブラリ (picamera2を推奨) ---
try:
    from picamera2 import Picamera2
except ImportError:
    print("Warning: picamera2 not found. Install it for camera functionality.")

# --- 設定値 ---
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    print("エラー: GOOGLE_API_KEYが設定されていません。")
    exit(1)

# API設定
genai.configure(api_key=GOOGLE_API_KEY)
MODEL_NAME = "gemini-flash-lite-latest"
gemini_model = genai.GenerativeModel(MODEL_NAME)

# Whisper設定
# tiny, base, small, medium, largeから選択
WHISPER_MODEL = WhisperModel("tiny", device="cpu", compute_type="int8")
SAMPLE_RATE = 44100  # ハードウェアでサポートされているレート
CHUNK_SIZE = 1280    # mimi.pyと同じサイズ
MICROPHONE_INDEX = 1  # 使用するマイクデバイスのインデックスを指定してください

# AquesTalkPi設定
AQUESTALK_PATH = "/home/pi/pivot/aques/AquesTalkPi"

# カメラ設定
IMAGE_PATH = r"/home/pi/pivot/temp_capture.jpg" # 撮影した画像を保存する一時ファイル
DEFAULT_PROMPT = "この画像について何か尋ねていますか？"

# --- Gemini チャットセッション（記憶保持用） ---
# システム指示は、最初のメッセージに含めるか、Geminiモデルに渡す（ここでは最初のメッセージに含めます）
CHAT = gemini_model.start_chat(history=[])
print(f"✅ Geminiモデル: {MODEL_NAME} でチャットセッションを開始しました。")

# --- Flask アプリケーション設定 ---
app = Flask(__name__)
CORS(app)

# グローバル変数（音声認識制御用）
recognition_active = False
audio_stream = None

# --- AquesTalkPi 音声合成関数 ---
def speak(text):
    """AquesTalkPiを使ってテキストを音声に変換し、aplayで出力する."""
    # コマンドインジェクションを防ぐため、subprocess.runを使用
    try:
        # AquesTalkPiコマンドとaplayコマンドをパイプで接続
        process = subprocess.Popen(
            [AQUESTALK_PATH, text],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        subprocess.run(
            ['aplay'],
            stdin=process.stdout,
            check=True
        )
        process.stdout.close() # パイプを閉じる
        process.wait()
    except FileNotFoundError:
        print(f"エラー: AquesTalkPiまたはaplayが見つかりません。パスを確認してください: {AQUESTALK_PATH}")
    except Exception as e:
        print(f"音声出力中にエラーが発生しました: {e}")

# --- オーディオ処理関数 ---
def enhance_audio(audio_data, sample_rate=44100, gain=2.0):
    """オーディオデータのボリューム増幅"""
    try:
        # ボリューム増幅
        amplified = audio_data * gain
        amplified = np.clip(amplified, -32768, 32767).astype(np.int16)
        return amplified
    except Exception as e:
        print(f"オーディオ強化エラー: {e}")
        return audio_data

# --- カメラ撮影関数 ---
def take_picture(path=IMAGE_PATH):
    """Raspberry Pi Camera V1 (Picamera2) で画像を撮影する."""
    try:
        # Picamera2のインスタンスを初期化
        # V1カメラの解像度に合わせて設定を調整する必要があるかもしれません
        picam2 = Picamera2()
        config = picam2.create_still_configuration(main={"size": (640, 480)}) # V1カメラは最大5MP
        picam2.configure(config)
        picam2.start()
        time.sleep(2) # オートフォーカスと露出調整を待つ
        
        picam2.capture_file(path)
        picam2.stop()
        print(f"📸 画像を撮影し、{path}に保存しました。")
        return True
    except NameError:
        print("エラー: picamera2ライブラリが見つかりません。カメラ機能はスキップされます。")
        return False
    except Exception as e:
        print(f"カメラ撮影中にエラーが発生しました: {e}")
        return False

# --- メイン処理関数 ---
def process_request(user_text, image_path):
    """Gemini APIにリクエストを送信し、応答を音声で出力する."""
    
    # 画像ファイルを開く
    try:
        image = Image.open(image_path)
        print("画像の読み込みが完了しました。")
    except Exception:
        print("画像ファイルが見つからないか、読み込めません。テキストのみで送信します。")
        image = None

    # プロンプトを構築
    # ここにRAG.txtの内容などの事前プロンプトがあれば追加する
    
    # ユーザー入力が空の場合、デフォルトのプロンプトを使用
    if not user_text.strip():
        full_prompt = DEFAULT_PROMPT
    else:
        full_prompt = user_text

    print(f"\n🧠 Geminiに送信: {full_prompt}")

    # マルチモーダルコンテンツリスト
    contents = [full_prompt]
    if image:
        contents.append(image)

    # APIリクエスト実行（記憶保持のため chat.send_message を使用）
    try:
        response = CHAT.send_message(contents)
        ai_response = response.text
        print(f"🤖 AI応答: {ai_response}")
        speak(ai_response) # 音声で読み上げ
    except Exception as e:
        error_message = f"Gemini APIエラー: {e}"
        print(error_message)
        speak("ごめんなさい。AIとの通信に失敗しました。")


# --- HTTP エンドポイント ---
@app.route('/clicked', methods=['POST'])
def handle_click():
    """HTTPでPOSTリクエストを受け取ると音声認識を開始"""
    global recognition_active
    
    try:
        print("🌐 HTTPリクエストを受信しました！音声認識を開始します...")
        
        # 音声認識開始
        recognition_active = True
        result = start_voice_recognition()
        
        return jsonify({
            "status": "success",
            "message": "音声認識完了",
            "transcript": result.get("transcript", ""),
            "ai_response": result.get("ai_response", "")
        })
    
    except Exception as e:
        print(f"エラー: {e}")
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500

def start_voice_recognition():
    """Whisperを使って音声認識を実行してAI応答まで処理"""
    global audio_stream
    
    if not audio_stream:
        raise Exception("オーディオシステムが初期化されていません")
    
    print("🎙️  何かお話しください... (5秒間録音)")
    
    # 音声データを収集
    frames = []
    recording_duration = 5  # 5秒間録音
    total_frames = int(SAMPLE_RATE / CHUNK_SIZE * recording_duration)
    
    try:
        for i in range(total_frames):
            data = audio_stream.read(CHUNK_SIZE, exception_on_overflow=False)
            frames.append(data)
    except Exception as e:
        print(f"音声録音エラー: {e}")
        return {
            "transcript": "",
            "ai_response": "音声録音に失敗しました。"
        }
    
    print("🔄 Whisperで音声認識中...")
    
    # 音声データをnumpy配列に変換
    audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
    
    # 音声強化
    enhanced_audio = enhance_audio(audio_data, SAMPLE_RATE, gain=2.0)
    
    # float32に正規化（Whisperの入力形式）
    audio_float = enhanced_audio.astype(np.float32) / 32768.0
    
    try:
        # Whisperで音声認識
        segments, info = WHISPER_MODEL.transcribe(audio_float, beam_size=5, language="ja")
        
        # 認識結果を取得
        user_transcript = ""
        for segment in segments:
            user_transcript += segment.text + " "
        
        user_transcript = user_transcript.strip()
        
        if user_transcript:
            print(f"📝 認識結果: {user_transcript}")
            
            # 画像撮影
            take_picture()
            
            # AI応答を生成（画像付きで）
            ai_response = ""
            try:
                response_data = process_request(user_transcript, IMAGE_PATH)
                ai_response = response_data.get("ai_response", "AI応答の取得に失敗しました")
                print(f"🤖 AI応答: {ai_response}")
                speak(ai_response)
            except Exception as e:
                ai_response = f"AIエラー: {e}"
                speak("ごめんなさい。AIとの通信に失敗しました。")
                print(f"AIエラー詳細: {e}")
            
            return {
                "transcript": user_transcript,
                "ai_response": ai_response
            }
        else:
            print("⚠️ 発言が検出されませんでした。")
            speak("聞き取れませんでした。")
            return {
                "transcript": "",
                "ai_response": "聞き取れませんでした。"
            }
            
    except Exception as e:
        print(f"Whisper音声認識エラー: {e}")
        speak("音声認識に失敗しました。")
        return {
            "transcript": "",
            "ai_response": "音声認識に失敗しました。"
        }

# --- メインループ (HTTP サーバー) ---
def main_loop():
    global audio_stream
    
    # PyAudio設定
    p = pyaudio.PyAudio()
    audio_stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE,
        input_device_index=MICROPHONE_INDEX,
    )
    
    print(f"\n🤖 Whisper音声認識システム起動")
    print(f"🎤 HTTPサーバー起動中...")
    print(f"🌐 http://pi.local:8100/clicked にPOSTリクエストを送信してください")
    
    # HTTPサーバーを起動
    try:
        app.run(host='0.0.0.0', port=8100, debug=False)
    finally:
        # クリーンアップ
        audio_stream.stop_stream()
        audio_stream.close()
        p.terminate()



if __name__ == "__main__":
    main_loop()