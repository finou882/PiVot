#!/usr/bin/env python3

from typing import Optional, List, Tuple, Any
from picamera2 import Picamera2
from datetime import datetime
import time
import os
from pathlib import Path
import subprocess
import shutil
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import soundfile as sf
import warnings
import sounddevice as sd
import librosa
import numpy as np
import re
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.error import URLError

RECORDING_SAMPLE_RATE = 48000
TARGET_SAMPLE_RATE = 16000


os.environ["ORT_DISABLE_ALL_PROVIDERS"] = "0"
warnings.filterwarnings("ignore", category=UserWarning, module="onnxruntime")

# USBマイクのネイティブサンプルレート設定
sd.default.samplerate = RECORDING_SAMPLE_RATE
sd.default.channels = 1

# .envファイルから環境変数を読み込む
load_dotenv()

# Gemini APIの設定
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

# ウェイクワードのリファレンスディレクトリ（16kHzにリサンプリング済み）
VOICE_EXAMPLES_DIR = "./voice_examples_16k"
WAKE_THRESHOLD = 0.04  # 検出閾値（小さいほど厳格、大きいほど緩い）
RECORDING_DURATION = 5  # プロンプト録音時間（秒）
REFERENCE_AUDIO_LENGTH = 2.5  # リファレンス音声の統一長（秒）
RAG_PROMPT_FILE = "./rag_prompt.txt"  # RAGプロンプトファイル
PHOTO_DIR = "./Past_Photo"  # 写真保存ディレクトリ
PROMPT_DIR = "./Past_Prompt"  # 音声プロンプト保存ディレクトリ
AQUESTALK_PATH = "./aquestalkpi/AquesTalkPi"
AQUESTALK_DEVICE = "plughw:1,0"
SERVO_API_BASE_URL = "http://172.20.10.3"
SERVO_AXIS_CHANNEL_MAP = {"x": 0, "y": 1}
SERVO_MIN_ANGLE = 0
SERVO_MAX_ANGLE = 180
SERVO_COMMAND_PATTERN = re.compile(r'req\.servo\s*\(([^)]*)\)', re.IGNORECASE)
SERVO_AXIS_PATTERN = re.compile(r'axis\s*=\s*[\'"]?\s*([xy])', re.IGNORECASE)
SERVO_ANGLE_PATTERN = re.compile(r'angle\s*(?:=|:)\s*([-+]?\s*\d+)', re.IGNORECASE)

# 音声検出パラメータ
VAD_SILENCE_THRESHOLD = 0.01  # 無音判定の閾値（RMS）
VAD_SILENCE_DURATION = 1.5  # この秒数無音が続いたら停止（秒）
VAD_MIN_DURATION = 0.5  # 最低録音時間（秒）
VAD_CHUNK_SIZE = 4800  # 音声チャンクサイズ（サンプル数、約0.1秒分）


def take_photo(filename: Optional[str] = None) -> str:
    try:
        os.makedirs(PHOTO_DIR, exist_ok=True)
        picam2 = Picamera2()
        camera_config = picam2.create_still_configuration()
        picam2.configure(camera_config)
        picam2.start()
        time.sleep(2)
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"photo_{timestamp}.jpg"
        
        filepath = os.path.join(PHOTO_DIR, filename)
        picam2.capture_file(filepath)
        print(f"写真を保存しました: {filepath}")
        
        picam2.stop()
        picam2.close()
        
        return filepath
    except Exception as e:
        print(f"エラー: 写真の撮影に失敗しました: {e}")
        raise RuntimeError(f"写真の撮影に失敗しました: {e}") from e


def load_rag_prompt() -> str:
    if os.path.exists(RAG_PROMPT_FILE):
        with open(RAG_PROMPT_FILE, 'r', encoding='utf-8') as f:
            rag_content = f.read().strip()
            if rag_content:
                print(f"RAGプロンプトを読み込みました（{len(rag_content)}文字）")
                return rag_content
    return ""


def analyze_photo_with_gemini(image_path: str, prompt: str = "", use_rag: bool = True) -> str:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"画像ファイルが見つかりません: {image_path}")
    
    try:
        image = Image.open(image_path)
        
        rag_prompt = ""
        if use_rag:
            rag_prompt = load_rag_prompt()
        
        if rag_prompt:
            if rag_prompt.strip().endswith("/////"):
                full_prompt = f"""{rag_prompt}
{prompt}""" if prompt else rag_prompt
            else:
                full_prompt = f"""{rag_prompt}

/////
{prompt}""" if prompt else f"""{rag_prompt}

/////"""
        else:
            full_prompt = prompt if prompt else "この画像について教えてください。"
        
        print(f"\nGemini AIで画像を分析中...")
        print(f"プロンプト: {prompt}")
        if rag_prompt:
            print(f"（RAGコンテキスト: {len(rag_prompt)}文字）")
        
        response = model.generate_content([full_prompt, image])
        
        return response.text
    except Exception as e:
        print(f"エラー: Gemini APIの呼び出しに失敗しました: {e}")
        raise RuntimeError(f"Gemini APIの呼び出しに失敗しました: {e}") from e


def synthesize_speech(text: str) -> None:
    if not text:
        return

    try:
        clean_text = text.replace("\n", " ").strip()
        if not clean_text:
            return

        if not os.path.exists(AQUESTALK_PATH):
            print(f"エラー: 音声合成バイナリが見つかりません: {AQUESTALK_PATH}")
            return

        if shutil.which("aplay") is None:
            print("エラー: aplay コマンドが見つかりません")
            return

        tts_result = subprocess.run(
            [AQUESTALK_PATH, clean_text],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        if tts_result.returncode != 0:
            error_msg = tts_result.stderr.decode(errors="ignore") if tts_result.stderr else "Unknown error"
            print(f"エラー: AquesTalkPi の実行に失敗しました: {error_msg.strip()}")
            return

        if not tts_result.stdout:
            print("エラー: AquesTalkPi から音声データが生成されませんでした")
            return

        aplay_result = subprocess.run(
            ["aplay", "-D", AQUESTALK_DEVICE],
            input=tts_result.stdout,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

        if aplay_result.returncode != 0:
            error_msg = aplay_result.stderr.decode(errors="ignore") if aplay_result.stderr else "Unknown error"
            print(f"エラー: aplay の再生に失敗しました: {error_msg.strip()}")
    except Exception as e:
        print(f"エラー: 音声合成に失敗しました: {e}")


def send_servo_command(axis: str, angle: int) -> None:
    channel = SERVO_AXIS_CHANNEL_MAP.get(axis)
    if channel is None:
        print(f"警告: 未対応の軸 {axis} を受信しました")
        return

    clamped_angle = max(SERVO_MIN_ANGLE, min(SERVO_MAX_ANGLE, angle))
    if clamped_angle != angle:
        print(f"角度{angle}を{clamped_angle}に補正しました")

    query = urlencode({"ch": channel, "angle": clamped_angle})
    url = f"{SERVO_API_BASE_URL}/servo?{query}"

    try:
        with urlopen(url, timeout=3) as response:
            response.read()
        print(f"サーボ送信成功: axis={axis}, ch={channel}, angle={clamped_angle}")
    except URLError as exc:
        print(f"エラー: サーボ送信に失敗しました ({url}): {exc}")


def handle_servo_commands(response_text: str) -> str:
    cleaned_lines: List[str] = []

    for raw_line in response_text.splitlines():
        for match in SERVO_COMMAND_PATTERN.finditer(raw_line):
            args = match.group(1)
            axis_match = SERVO_AXIS_PATTERN.search(args)
            angle_match = SERVO_ANGLE_PATTERN.search(args)

            if not axis_match or not angle_match:
                print(f"警告: サーボコマンドを解析できませんでした: {match.group(0)}")
                continue

            axis = axis_match.group(1).lower()

            try:
                angle_str = angle_match.group(1).replace(' ', '')
                angle = int(angle_str)
            except ValueError:
                print(f"警告: 角度の解析に失敗しました: {match.group(0)}")
                continue

            send_servo_command(axis, angle)

        cleaned_line = SERVO_COMMAND_PATTERN.sub('', raw_line).strip()
        if cleaned_line:
            cleaned_lines.append(cleaned_line)

    return "\n".join(cleaned_lines)


def take_photo_and_analyze(prompt: str = "") -> Tuple[str, str]:
    print("=" * 50)
    print("写真撮影とAI分析を開始します")
    print("=" * 50)
    
    photo_path = take_photo()
    result = analyze_photo_with_gemini(photo_path, prompt)
    
    print("\n" + "=" * 50)
    print("Gemini AIの分析結果:")
    print("=" * 50)
    print(result)
    print("=" * 50)
    speech_text = handle_servo_commands(result)
    synthesize_speech(speech_text)
    
    return photo_path, result


def record_voice_prompt(duration: float = RECORDING_DURATION, existing_stream: Optional[Any] = None, use_vad: bool = True) -> Optional[str]:
    if duration <= 0:
        raise ValueError(f"durationは正の数である必要があります: {duration}")
    
    os.makedirs(PROMPT_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(PROMPT_DIR, f"prompt_{timestamp}.wav")
    
    if use_vad:
        print(f"\n音声を録音します（最大{duration}秒、無音で自動停止）...")
        print("話し始めてください...")
        
        audio_data = []
        silent_samples = 0
        silence_samples_needed = int(VAD_SILENCE_DURATION * RECORDING_SAMPLE_RATE)
        min_samples = int(VAD_MIN_DURATION * RECORDING_SAMPLE_RATE)
        max_samples = int(duration * RECORDING_SAMPLE_RATE)
        
        if existing_stream is None:
            print("エラー: 音声検出モードでは既存のストリームが必要です")
            return None
        
        started = False
        
        while len(audio_data) < max_samples:
            chunk, _ = existing_stream.read(VAD_CHUNK_SIZE)
            chunk_audio = chunk[:, 0]
            audio_data.extend(chunk_audio)
            
            rms = np.sqrt(np.mean(chunk_audio ** 2))
            
            if not started and rms > VAD_SILENCE_THRESHOLD:
                started = True
                print("🎤 録音中...", end='', flush=True)
            
            if started:
                if rms < VAD_SILENCE_THRESHOLD:
                    silent_samples += len(chunk_audio)
                    progress = int((silent_samples / silence_samples_needed) * 10)
                    print(f"\r🎤 録音中... {'.' * progress}{' ' * (10 - progress)}", end='', flush=True)
                else:
                    silent_samples = 0
                    print(f"\r🎤 録音中...          ", end='', flush=True)
                
                if silent_samples >= silence_samples_needed and len(audio_data) >= min_samples:
                    print(f"\r✓ 無音を検出、録音終了（{len(audio_data) / RECORDING_SAMPLE_RATE:.1f}秒）")
                    break
        
        audio = np.array(audio_data)
    else:
        print(f"\n{duration}秒間プロンプトを録音します...")
        print("話し始めてください...")
        
        if existing_stream is not None:
            samples_needed = int(duration * RECORDING_SAMPLE_RATE)
            audio_data = []
            
            while len(audio_data) < samples_needed:
                chunk, _ = existing_stream.read(min(12000, samples_needed - len(audio_data)))
                audio_data.extend(chunk[:, 0])
            
            audio = np.array(audio_data[:samples_needed])
        else:
            audio = sd.rec(int(duration * RECORDING_SAMPLE_RATE), 
                           samplerate=RECORDING_SAMPLE_RATE, 
                           channels=1, 
                           dtype='float32')
            sd.wait()
            audio = audio[:, 0]
    
    audio_16k = librosa.resample(audio, 
                                  orig_sr=RECORDING_SAMPLE_RATE, 
                                  target_sr=TARGET_SAMPLE_RATE)
    
    sf.write(filename, audio_16k, TARGET_SAMPLE_RATE)
    
    if not use_vad:
        print(f"録音完了: {filename}")
    return filename


def speech_to_text_with_gemini(audio_path: str) -> str:
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"音声ファイルが見つかりません: {audio_path}")
    
    try:
        print("音声をテキストに変換中...")
        
        audio_file = genai.upload_file(path=audio_path)
        response = model.generate_content([
            "この音声を正確に文字起こししてください。テキストのみを返してください。また、意味が読み取れない部分があれば意訳をお願いします。",
            audio_file
        ])
        
        text = response.text.strip()
        print(f"認識されたテキスト: {text}")
        
        audio_file.delete()
        
        return text
    except Exception as e:
        print(f"エラー: 音声のテキスト変換に失敗しました: {e}")
        raise RuntimeError(f"音声のテキスト変換に失敗しました: {e}") from e


def take_photo_and_analyze_with_voice() -> None:
    import lwake.features as features
    
    print("=" * 50)
    print("音声認識モードを開始します")
    print(f"ウェイクワードを言ってください...")
    print("=" * 50)
    
    print("リファレンス音声を読み込み中...")
    reference_features = []
    for i in range(1, 5):
        ref_path = f"{VOICE_EXAMPLES_DIR}/Sample{i}.wav"
        if os.path.exists(ref_path):
            feat = features.extract_embedding_features(path=ref_path)
            reference_features.append((f"Sample{i}.wav", feat))
            print(f"  {ref_path} 読み込み完了")
    
    if not reference_features:
        print("エラー: リファレンス音声が見つかりません")
        return
    
    print(f"\n{len(reference_features)}個のリファレンス音声を読み込みました")
    print(f"バッファサイズ: {REFERENCE_AUDIO_LENGTH + 0.5}秒")
    print(f"閾値: {WAKE_THRESHOLD}")
    print("\nウェイクワード検出を開始します...")
    
    buffer_duration = REFERENCE_AUDIO_LENGTH + 0.5
    slide_duration = 0.25
    
    buffer_samples = int(buffer_duration * RECORDING_SAMPLE_RATE)
    slide_samples = int(slide_duration * RECORDING_SAMPLE_RATE)
    
    audio_buffer = np.zeros(buffer_samples, dtype=np.float32)
    
    try:
        with sd.InputStream(samplerate=RECORDING_SAMPLE_RATE, channels=1, dtype=np.float32) as stream:
            while True:
                data, overflowed = stream.read(slide_samples)
                
                chunk = data[:, 0]
                
                audio_buffer = np.roll(audio_buffer, -len(chunk))
                audio_buffer[-len(chunk):] = chunk
                
                audio_16k = librosa.resample(audio_buffer, 
                                             orig_sr=RECORDING_SAMPLE_RATE, 
                                             target_sr=TARGET_SAMPLE_RATE)
                
                try:
                    feat = features.extract_embedding_features(y=audio_16k, sample_rate=TARGET_SAMPLE_RATE)
                except Exception as e:
                    continue
                
                detected = False
                min_distance = float('inf')
                best_match = None
                
                for ref_name, ref_feat in reference_features:
                    distance = features.dtw_cosine_normalized_distance(feat, ref_feat)
                    
                    if distance < min_distance:
                        min_distance = distance
                        best_match = ref_name
                    
                    if distance < WAKE_THRESHOLD:
                        print(f"\n✓ ウェイクワード検出! ({ref_name}, 距離: {distance:.4f})")
                        detected = True
                        break
                
                if not detected and np.random.random() < 0.1:
                    print(f"  [デバッグ] 最小距離: {min_distance:.4f} ({best_match})", end='\r')
                
                if detected:
                    prompt_audio = record_voice_prompt(existing_stream=stream)
                    prompt_text = speech_to_text_with_gemini(prompt_audio)
                    
                    print("\n写真を撮影します...")
                    photo_path = take_photo()
                    
                    result = analyze_photo_with_gemini(photo_path, prompt_text)
                    
                    print("\n" + "=" * 50)
                    print("Gemini AIの分析結果:")
                    print("=" * 50)
                    print(result)
                    print("=" * 50)
                    speech_text = handle_servo_commands(result)
                    synthesize_speech(speech_text)
                    
                    print(f"音声プロンプトを保存しました: {prompt_audio}")
                    
                    audio_buffer = np.zeros(buffer_samples, dtype=np.float32)
                    
                    print(f"\n再度ウェイクワードを言ってください...")
    
    except KeyboardInterrupt:
        print("\n\n音声認識を終了しました")
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    take_photo_and_analyze_with_voice()