import os
import subprocess
import time
import threading
import numpy as np
import re

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from PIL import Image

# サーボ制御機能と応答解析をインポート
from response_parser import extract_response_text, extract_code_blocks, execute_action_code

# --- 音声処理ライブラリ ---
import pyaudio
from faster_whisper import WhisperModel
import wave

# --- サーボ制御ライブラリ ---
from servo_control import cam_move, url, init_gpio, cleanup_gpio

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
ROBOTICS_MODEL_NAME = "gemini-2.0-flash-exp"  # Gemini-Robotics-ER model
gemini_model = genai.GenerativeModel(MODEL_NAME)
robotics_model = genai.GenerativeModel(ROBOTICS_MODEL_NAME)

# Whisper設定
# tiny, base, small, medium, largeから選択（baseは日本語認識がより良い）
# Whisper設定
# tiny, base, small, medium, largeから選択
WHISPER_MODEL = WhisperModel("tiny", device="cpu", compute_type="int8")
SAMPLE_RATE = 44100  # ハードウェアでサポートされているレート
CHUNK_SIZE = 1280    # mimi.pyと同じサイズ
MICROPHONE_INDEX = 1  # 使用するマイクデバイスのインデックスを指定してください

# AquesTalkPi設定
AQUESTALK_PATH = "/home/pi/pivot/aques/AquesTalkPi"

# カメラ設定
# スクリプトと同じディレクトリに一時画像を保存
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
IMAGE_PATH = os.path.join(SCRIPT_DIR, "temp_capture.jpg")
DEFAULT_PROMPT = "この画像について何か尋ねていますか？"

# --- Gemini チャットセッション（記憶保持用） ---
# システム指示は、最初のメッセージに含めるか、Geminiモデルに渡す（ここでは最初のメッセージに含めます）
CHAT = gemini_model.start_chat(history=[])
print(f"✅ Geminiモデル: {MODEL_NAME} でチャットセッションを開始しました。")
print(f"✅ Robotics-ERモデル: {ROBOTICS_MODEL_NAME} を初期化しました。")

# --- Flask アプリケーション設定 ---
app = Flask(__name__)
CORS(app)

# グローバル変数（音声認識制御用）
recognition_active = False
audio_stream = None
recognition_lock = threading.Lock()

# --- AquesTalkPi 音声合成関数 ---
def speak(text):
    """AquesTalkPiを使ってテキストを音声に変換し、aplayで出力する."""
    # XMLタグを除去して音声合成用のクリーンなテキストにする
    clean_text = text
    # <respose>タグを除去（スペルミス版）
    clean_text = re.sub(r'</?respose>', '', clean_text)
    # <response>タグを除去（正しいスペル版）
    clean_text = re.sub(r'</?response>', '', clean_text)
    # <code>タグを除去
    clean_text = re.sub(r'</?code>', '', clean_text)
    # その他のXMLタグも除去
    clean_text = re.sub(r'<[^>]+>', '', clean_text)
    # 余分な空白を除去
    clean_text = clean_text.strip()
    
    print(f"🔊 音声合成テキスト（タグ除去後）: {clean_text}")
    
    # 空のテキストの場合は音声合成しない
    if not clean_text:
        print("⚠️ 音声合成するテキストが空です")
        return
    
    # コマンドインジェクションを防ぐため、subprocess.runを使用
    try:
        # AquesTalkPiコマンドとaplayコマンドをパイプで接続
        process = subprocess.Popen(
            [AQUESTALK_PATH, clean_text],
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

def check_repeated_words(text, threshold=3):
    """
    テキスト内で同じ語彙が連続して出現するかをチェック
    
    Args:
        text (str): チェックするテキスト
        threshold (int): 連続出現の閾値（デフォルト: 3）
    
    Returns:
        bool: 同じ語彙がthreshold回以上連続している場合True
    """
    if not text or not text.strip():
        return False
    
    # テキストを語彙に分割（スペースまたは句読点で区切る）
    import re
    words = re.findall(r'[ぁ-んァ-ヶー一-龠a-zA-Z0-9]+', text)
    
    if len(words) < threshold:
        return False
    
    # 連続する同じ語彙をカウント
    consecutive_count = 1
    prev_word = words[0] if words else ""
    
    for word in words[1:]:
        if word == prev_word:
            consecutive_count += 1
            if consecutive_count >= threshold:
                print(f"🔄 同じ語彙の連続検出: '{word}' x {consecutive_count}")
                return True
        else:
            consecutive_count = 1
            prev_word = word
    
    return False

def get_text_input():
    """
    コンソールからテキスト入力を取得
    
    Returns:
        str: 入力されたテキスト
    """
    print("📝 テキスト入力モードに切り替えました。")
    print("💡 メッセージを入力してEnterを押してください（'quit'で終了）:")
    
    try:
        user_input = input("👤 > ")
        if user_input.lower() in ['quit', 'exit', '終了', 'やめる']:
            return ""
        return user_input.strip()
    except (KeyboardInterrupt, EOFError):
        print("\n⚠️ 入力がキャンセルされました。")
        return ""

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

# --- AI応答パース関数 ---
def parse_ai_response(response_text):
    """
    AI応答からタグを抽出して分離する
    
    Parameters:
    -----------
    response_text : str
        AI応答の全文
    
    Returns:
    --------
    dict
        {
            'response': str - ユーザーへの応答テキスト（<response>タグ内）,
            'code': str - 実行するコード（<code>タグ内）,
            'raw': str - タグを除去した全文
        }
    """
    result = {
        'response': '',
        'code': '',
        'raw': response_text
    }
    
    # <respose>タグの抽出（スペルミス版）
    respose_match = re.search(r'<respose>(.*?)</respose>', response_text, re.DOTALL)
    if respose_match:
        result['response'] = respose_match.group(1).strip()
    
    # <response>タグの抽出（正しいスペル版）
    response_match = re.search(r'<response>(.*?)</response>', response_text, re.DOTALL)
    if response_match:
        result['response'] = response_match.group(1).strip()
    
    # <code>タグの抽出
    code_match = re.search(r'<code>(.*?)</code>', response_text, re.DOTALL)
    if code_match:
        result['code'] = code_match.group(1).strip()
    
    # タグを除去した全文を取得
    raw_text = response_text
    raw_text = re.sub(r'<respose>.*?</respose>', '', raw_text, flags=re.DOTALL)
    raw_text = re.sub(r'<response>.*?</response>', '', raw_text, flags=re.DOTALL)
    raw_text = re.sub(r'<code>.*?</code>', '', raw_text, flags=re.DOTALL)
    result['raw'] = raw_text.strip()
    
    return result


def execute_ai_code(code_string):
    """
    AI応答から抽出したコードを安全に実行する
    
    Parameters:
    -----------
    code_string : str
        実行するPythonコード
    
    Returns:
    --------
    bool
        実行が成功した場合True, 失敗した場合False
    """
    if not code_string:
        return True
    
    print(f"🔧 コード実行: {code_string}")
    
    # セキュリティ: コードの検証
    # 許可された関数呼び出しのみを実行
    allowed_patterns = [
        r"cam_move\s*\(\s*shaft\s*=\s*['\"](?:x|z)['\"]\s*,\s*angle\s*=\s*\d+(?:\.\d+)?\s*\)",
        r"url\s*\(\s*['\"]https?://[^'\"]+['\"]\s*\)"
    ]
    
    # コードを行ごとに分割して検証
    lines = [line.strip() for line in code_string.split('\n') if line.strip()]
    for line in lines:
        valid = False
        for pattern in allowed_patterns:
            if re.match(pattern, line):
                valid = True
                break
        if not valid:
            print(f"❌ セキュリティエラー: 許可されていないコード: {line}")
            return False
    
    # 安全な実行環境を準備
    # cam_move と url 関数のみを許可
    allowed_globals = {
        'cam_move': cam_move,
        'url': url,
        '__builtins__': {}  # 組み込み関数を制限
    }
    
    try:
        # コードを実行
        exec(code_string, allowed_globals, {})
        print("✅ コード実行完了")
        return True
    except Exception as e:
        print(f"❌ コード実行エラー: {e}")
        return False

# --- Robotics-ER画像解析関数 ---
def analyze_image_with_robotics_er(image):
    """
    Gemini-Robotics-ERモデルで画像を解析する
    
    Parameters:
    -----------
    image : PIL.Image
        解析する画像
    
    Returns:
    --------
    str
        画像の解析結果テキスト
    """
    try:
        print("🤖 Robotics-ERモデルで画像を解析中...")
        # Robotics-ERモデルに画像を送信して解析
        prompt = "この画像に写っているものを詳しく説明してください。物体の位置、色、形状、空間的な関係性を含めて説明してください。"
        response = robotics_model.generate_content([prompt, image])
        analysis_result = response.text
        print(f"🔍 Robotics-ER解析結果: {analysis_result[:200]}..." if len(analysis_result) > 200 else f"🔍 Robotics-ER解析結果: {analysis_result}")
        return analysis_result
    except Exception as e:
        print(f"⚠️ Robotics-ER解析エラー: {e}")
        return ""

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

    # RAG.txtの内容を読み込み
    rag_content = ""
    # スクリプトと同じディレクトリのRAG.txtを探す
    script_dir = os.path.dirname(os.path.abspath(__file__))
    rag_path = os.path.join(script_dir, "RAG.txt")
    
    try:
        with open(rag_path, 'r', encoding='utf-8') as f:
            rag_content = f.read()
        print("📚 RAG.txtを読み込みました")
    except Exception as e:
        print(f"⚠️ RAG.txt読み込みエラー: {e}")
        rag_content = ""
    
    # プロンプトを構築（RAG.txt + ユーザー入力）
    if not user_text.strip():
        user_input = DEFAULT_PROMPT
    else:
        user_input = user_text
    
    # RAG.txtの内容を前置してプロンプトを作成
    if rag_content:
        full_prompt = f"{rag_content}\n\n//What users say//\n{user_input}"
    else:
        full_prompt = user_input

    print(f"\n🧠 Geminiに送信: {user_input} (RAG付き: {bool(rag_content)})")

    # Robotics-ERモデルで画像を解析（画像がある場合）
    robotics_analysis = ""
    if image:
        robotics_analysis = analyze_image_with_robotics_er(image)
    
    # プロンプトにRobotics-ERの解析結果を追加
    if robotics_analysis:
        full_prompt = f"{full_prompt}\n\n//Robotics-ER Vision Analysis//\n{robotics_analysis}"
        print(f"✅ Robotics-ER解析結果をプロンプトに統合しました")

    # マルチモーダルコンテンツリスト
    contents = [full_prompt]
    if image:
        contents.append(image)

    # APIリクエスト実行（記憶保持のため chat.send_message を使用）
    try:
        response = CHAT.send_message(contents)
        ai_response = response.text
        print(f"🤖 AI応答（生）: {ai_response}")
        
        # <code>タグからアクションコードを抽出して実行
        code_blocks = extract_code_blocks(ai_response)
        if code_blocks:
            print(f"📝 {len(code_blocks)}個のアクションコードを検出")
            for i, code in enumerate(code_blocks, 1):
                print(f"   アクション {i}: {code}")
                print(f"🔧 アクションコード実行開始...")
                execute_action_code(code)
                print(f"✅ アクション {i} 実行完了")
        else:
            print("📝 <code>タグが見つかりません")
        
        # <response>タグから音声出力用テキストを抽出
        speech_text = extract_response_text(ai_response)
        print(f"🗣️ 元のAI応答: {ai_response}")
        print(f"🗣️ 抽出された音声テキスト: {speech_text}")
        
        # 音声で読み上げ（タグを除去したテキスト）
        if speech_text:
            print(f"🔊 音声合成開始: {speech_text}")
            speak(speech_text)
        
        return {"status": "success", "ai_response": ai_response}
        # AI応答をパースする
        parsed = parse_ai_response(ai_response)
        
        # 応答テキストを取得（<response>タグがあればそれを使用、なければ全文）
        response_text = parsed['response'] if parsed['response'] else parsed['raw']
        
        # コードを実行
        if parsed['code']:
            print(f"📝 抽出されたコード: {parsed['code']}")
            execute_ai_code(parsed['code'])
        
        # 音声で読み上げ（応答テキストのみ）
        if response_text:
            print(f"🤖 AI応答（音声出力）: {response_text}")
            speak(response_text)
        
        return {"status": "success", "ai_response": ai_response, "spoken_text": response_text}
    except Exception as e:
        error_message = f"Gemini APIエラー: {e}"
        print(error_message)
        speak("ごめんなさい。AIとの通信に失敗しました。")
        return {"status": "error", "ai_response": "AIとの通信に失敗しました。"}



# --- HTTP エンドポイント ---
@app.route('/clicked', methods=['POST'])
def handle_click():
    """HTTPでPOSTリクエストを受け取ると音声認識を開始"""
    global recognition_active, recognition_lock

    # 同時実行を防止: 認識中は追加リクエストを無視する
    with recognition_lock:
        if recognition_active:
            print("⚠️ 既に音声認識中のためリクエストを無視します。")
            return jsonify({
                "status": "ignored",
                "message": "現在音声認識中です。後で試してください。",
                "transcript": "",
                "ai_response": ""
            }), 200
        # 認識を開始するフラグを立てる
        recognition_active = True

    try:
        print("🌐 HTTPリクエストを受信しました！音声認識を開始します...")
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

    finally:
        # 認識フラグを必ずクリアする
        with recognition_lock:
            recognition_active = False

@app.route('/text_input', methods=['POST'])
def handle_text_input():
    """HTTPでテキスト入力を受け取って処理"""
    try:
        # リクエストの詳細をログに出力
        print(f"🌐 Content-Type: {request.headers.get('Content-Type')}")
        print(f"🌐 Request Data: {request.data}")
        
        # JSONデータを取得
        data = request.get_json(force=True)  # force=Trueを追加
        print(f"🌐 Parsed JSON: {data}")
        
        if not data or 'text' not in data:
            print("❌ JSONにtextフィールドがありません")
            return jsonify({
                "status": "error",
                "message": "テキストが提供されていません。JSON形式で{\"text\": \"メッセージ\"}を送信してください。"
            }), 400
        
        user_text = data['text'].strip()
        if not user_text:
            print("❌ テキストが空です")
            return jsonify({
                "status": "error", 
                "message": "空のテキストです"
            }), 400
        
        print(f"📝 テキスト入力受信: {user_text}")
        
        # 画像撮影
        take_picture()
        
        # AI応答を生成
        try:
            response_data = process_request(user_text, IMAGE_PATH)
            return jsonify({
                "status": "success",
                "message": "テキスト処理完了", 
                "transcript": user_text,
                "ai_response": response_data.get("ai_response", "")
            })
        except Exception as e:
            print(f"AI処理エラー: {e}")
            return jsonify({
                "status": "error",
                "message": f"AI処理エラー: {e}"
            }), 500
            
    except ValueError as e:
        print(f"❌ JSON解析エラー: {e}")
        return jsonify({
            "status": "error",
            "message": f"JSON解析エラー: {str(e)}。正しいJSON形式で送信してください。"
        }), 400
    except Exception as e:
        print(f"❌ テキスト入力エラー: {e}")
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500

@app.route('/text_input', methods=['GET'])
def handle_text_input_get():
    """テキスト入力エンドポイントのテスト用GET"""
    return jsonify({
        "status": "info",
        "message": "テキスト入力エンドポイントです。POST方式で{\"text\": \"メッセージ\"}を送信してください。",
        "example": "curl -X POST http://IPアドレス:8100/text_input -H \"Content-Type: application/json\" -d \"{\\\"text\\\": \\\"テストメッセージ\\\"}\""
    })

def start_voice_recognition():
    """Whisperを使って音声認識を実行してAI応答まで処理"""
    global audio_stream
    
    if not audio_stream:
        raise Exception("オーディオシステムが初期化されていません")
    
    print(f"🎙️  何かお話しください... (7秒間録音, {SAMPLE_RATE}Hz)")
    
    # 音声データを収集
    frames = []
    recording_duration = 7  # 7秒間録音（長めに設定）
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
    
    # 音声レベルチェック
    audio_max = np.max(np.abs(audio_data))
    audio_mean = np.mean(np.abs(audio_data))
    print(f"📊 音声レベル - 最大: {audio_max}, 平均: {audio_mean:.1f}")
    
    if audio_max < 100:
        print("⚠️ 音声レベルが非常に低いです。マイクの音量を確認してください。")
    
    # 音声強化（ゲインを上げる）
    enhanced_audio = enhance_audio(audio_data, SAMPLE_RATE, gain=5.0)
    
    # float32に正規化（Whisperの入力形式）
    audio_float = enhanced_audio.astype(np.float32) / 32768.0
    
    try:
        # Whisperで音声認識（日本語特化パラメータ）
        segments, info = WHISPER_MODEL.transcribe(
            audio_float, 
            beam_size=5, 
            language="ja",
            condition_on_previous_text=False,  # 前のテキストに依存しない
            temperature=0.0,  # 確定的な結果
            compression_ratio_threshold=2.4,  # 日本語用に調整
            log_prob_threshold=-1.0,  # ログ確率閾値を下げる
            no_speech_threshold=0.6  # 無音検出閾値を上げる
        )
        
        print(f"🌐 検出言語: {info.language} (確率: {info.language_probability:.2f})")
        
        # 認識結果を取得
        user_transcript = ""
        for segment in segments:
            print(f"📝 セグメント: '{segment.text}' (確率: {segment.avg_logprob:.2f})")
            user_transcript += segment.text + " "
        
        user_transcript = user_transcript.strip()
        
        if user_transcript:
            print(f"📝 認識結果: {user_transcript}")
            
            # 同じ語彙の連続をチェック
            if check_repeated_words(user_transcript, threshold=3):
                print("🔄 同じ語彙が3回以上連続しています。テキスト入力モードに切り替えます。")
                speak("同じ言葉が繰り返されています。テキスト入力モードに切り替えます。")
                
                # テキスト入力を取得
                text_input = get_text_input()
                if text_input:
                    user_transcript = text_input
                    print(f"📝 テキスト入力: {user_transcript}")
                else:
                    print("❌ テキスト入力がキャンセルされました。")
                    return {
                        "transcript": "",
                        "ai_response": "テキスト入力がキャンセルされました。"
                    }
            
            # 画像撮影
            take_picture()
            
            # AI応答を生成（画像付きで）
            ai_response = ""
            try:
                response_data = process_request(user_transcript, IMAGE_PATH)
                ai_response = response_data.get("ai_response", "AI応答の取得に失敗しました")
                print(f"🤖 AI完全応答: {ai_response}")
                # 音声出力はprocess_request内で実行済み
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
            print(f"🔍 デバッグ: 音声最大レベル={audio_max}, 平均レベル={audio_mean:.1f}")
            print("💡 ヒント: マイクに近づいて、はっきりと話してください")
            speak("聞き取れませんでした。もう少し大きな声でお話しください。")
            return {
                "transcript": "",
                "ai_response": "聞き取れませんでした。もう少し大きな声でお話しください。"
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
    
    # サーボ制御の初期化
    if init_gpio():
        print("✅ サーボ制御初期化成功")
    else:
        print("⚠️ サーボ制御初期化失敗 - シミュレーションモードで実行")
    
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
    print(f"🌐 音声認識: http://pi.local:8100/clicked にPOSTリクエスト")
    print("📝 テキスト入力: http://pi.local:8100/text_input にJSON POST {\"text\": \"メッセージ\"}")
    
    # HTTPサーバーを起動
    try:
        app.run(host='0.0.0.0', port=8100, debug=False)
    finally:
        # クリーンアップ
        print("🧹 システムクリーンアップ中...")
        cleanup_gpio()
        audio_stream.stop_stream()
        audio_stream.close()
        p.terminate()
        print("✅ クリーンアップ完了")



if __name__ == "__main__":
    main_loop()