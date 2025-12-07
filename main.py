#!/usr/bin/env python3
"""
PiCamera2を使用した写真撮影とGemini AIによる画像分析スクリプト
音声ウェイクワード検出機能付き
"""

from typing import Optional, List, Tuple, Any
from picamera2 import Picamera2
from datetime import datetime
import time
import os
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import soundfile as sf
import warnings
import sounddevice as sd
import librosa
import numpy as np

# 音声録音パラメータ（早期定義が必要）
RECORDING_SAMPLE_RATE = 48000  # 録音時のサンプルレート（Hz）
TARGET_SAMPLE_RATE = 16000  # 処理用サンプルレート（Hz）

# ONNXRuntimeのGPU警告を抑制（ラズパイではGPUが利用できないため）
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

# 音声検出パラメータ
VAD_SILENCE_THRESHOLD = 0.01  # 無音判定の閾値（RMS）
VAD_SILENCE_DURATION = 1.5  # この秒数無音が続いたら停止（秒）
VAD_MIN_DURATION = 0.5  # 最低録音時間（秒）
VAD_CHUNK_SIZE = 4800  # 音声チャンクサイズ（サンプル数、約0.1秒分）


def take_photo(filename: Optional[str] = None) -> str:
    """カメラで写真を撮影する
    
    Args:
        filename: 保存するファイル名（省略時はタイムスタンプ付き）
    
    Returns:
        str: 保存されたファイルのパス
        
    Raises:
        RuntimeError: カメラの初期化または撮影に失敗した場合
    """
    try:
        # 保存ディレクトリを作成
        os.makedirs(PHOTO_DIR, exist_ok=True)
        
        # カメラの初期化
        picam2 = Picamera2()
        
        # カメラ設定
        camera_config = picam2.create_still_configuration()
        picam2.configure(camera_config)
        
        # カメラの起動
        picam2.start()
        
        # カメラのウォームアップ（推奨）
        time.sleep(2)
        
        # ファイル名にタイムスタンプを使用
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"photo_{timestamp}.jpg"
        
        # フルパスを作成
        filepath = os.path.join(PHOTO_DIR, filename)
        
        # 写真を撮影
        picam2.capture_file(filepath)
        print(f"写真を保存しました: {filepath}")
        
        # カメラの停止
        picam2.stop()
        picam2.close()
        
        return filepath
    except Exception as e:
        print(f"エラー: 写真の撮影に失敗しました: {e}")
        raise RuntimeError(f"写真の撮影に失敗しました: {e}") from e


def load_rag_prompt() -> str:
    """RAGプロンプトを読み込む
    
    Returns:
        str: RAGプロンプト（存在しない場合は空文字列）
    """
    if os.path.exists(RAG_PROMPT_FILE):
        with open(RAG_PROMPT_FILE, 'r', encoding='utf-8') as f:
            rag_content = f.read().strip()
            if rag_content:
                print(f"RAGプロンプトを読み込みました（{len(rag_content)}文字）")
                return rag_content
    return ""


def analyze_photo_with_gemini(image_path: str, prompt: str = "この画像について詳しく説明してください。", use_rag: bool = True) -> str:
    """撮影した写真をGemini AIで分析する
    
    Args:
        image_path: 分析する画像のパス
        prompt: Geminiに送るプロンプト
        use_rag: RAGプロンプトを使用するか
    
    Returns:
        str: Geminiからの応答テキスト
        
    Raises:
        FileNotFoundError: 画像ファイルが見つからない場合
        RuntimeError: Gemini APIの呼び出しに失敗した場合
    """
    # 画像ファイルの存在確認
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"画像ファイルが見つかりません: {image_path}")
    
    try:
        # 画像を読み込む
        image = Image.open(image_path)
        
        # RAGプロンプトを読み込む
        rag_prompt = ""
        if use_rag:
            rag_prompt = load_rag_prompt()
        
        # プロンプトを構築
        if rag_prompt:
            full_prompt = f"""{rag_prompt}

---

ユーザーの質問: {prompt}"""
        else:
            full_prompt = prompt
        
        # Geminiで分析
        print(f"\nGemini AIで画像を分析中...")
        print(f"プロンプト: {prompt}")
        if rag_prompt:
            print(f"（RAGコンテキスト: {len(rag_prompt)}文字）")
        
        response = model.generate_content([full_prompt, image])
        
        return response.text
    except Exception as e:
        print(f"エラー: Gemini APIの呼び出しに失敗しました: {e}")
        raise RuntimeError(f"Gemini APIの呼び出しに失敗しました: {e}") from e


def take_photo_and_analyze(prompt: str = "この画像について詳しく説明してください。") -> Tuple[str, str]:
    """写真を撮影してGemini AIで分析する
    
    Args:
        prompt: Geminiに送るプロンプト
        
    Returns:
        Tuple[str, str]: (写真のパス, 分析結果)
    """
    print("=" * 50)
    print("写真撮影とAI分析を開始します")
    print("=" * 50)
    
    # 写真を撮影
    photo_path = take_photo()
    
    # Geminiで分析
    result = analyze_photo_with_gemini(photo_path, prompt)
    
    # 結果を表示
    print("\n" + "=" * 50)
    print("Gemini AIの分析結果:")
    print("=" * 50)
    print(result)
    print("=" * 50)
    
    return photo_path, result


def record_voice_prompt(duration: float = RECORDING_DURATION, existing_stream: Optional[Any] = None, use_vad: bool = True) -> Optional[str]:
    """音声でプロンプトを録音する（音声検出で自動停止）
    
    Args:
        duration: 最大録音時間（秒）
        existing_stream: 既存の入力ストリーム（Noneの場合は新規作成）
        use_vad: 音声検出を使用するか（True: 無音で自動停止, False: 固定時間録音）
    
    Returns:
        str: 録音したファイルのパス、またはNone（エラーの場合）
        
    Raises:
        ValueError: durationが無効な値の場合
    """
    # 入力値の検証
    if duration <= 0:
        raise ValueError(f"durationは正の数である必要があります: {duration}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"prompt_{timestamp}.wav"
    
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
            
            # RMS（音量）を計算
            rms = np.sqrt(np.mean(chunk_audio ** 2))
            
            # 音声が開始されたかチェック
            if not started and rms > VAD_SILENCE_THRESHOLD:
                started = True
                print("🎤 録音中...", end='', flush=True)
            
            # 無音判定（音声開始後のみ）
            if started:
                if rms < VAD_SILENCE_THRESHOLD:
                    silent_samples += len(chunk_audio)
                    # 進捗表示
                    progress = int((silent_samples / silence_samples_needed) * 10)
                    print(f"\r🎤 録音中... {'.' * progress}{' ' * (10 - progress)}", end='', flush=True)
                else:
                    silent_samples = 0
                    print(f"\r🎤 録音中...          ", end='', flush=True)
                
                # 無音が続いたら停止（最低録音時間を超えている場合）
                if silent_samples >= silence_samples_needed and len(audio_data) >= min_samples:
                    print(f"\r✓ 無音を検出、録音終了（{len(audio_data) / RECORDING_SAMPLE_RATE:.1f}秒）")
                    break
        
        audio = np.array(audio_data)
    else:
        print(f"\n{duration}秒間プロンプトを録音します...")
        print("話し始めてください...")
        
        if existing_stream is not None:
            # 既存のストリームから読み取る
            samples_needed = int(duration * RECORDING_SAMPLE_RATE)
            audio_data = []
            
            while len(audio_data) < samples_needed:
                chunk, _ = existing_stream.read(min(12000, samples_needed - len(audio_data)))
                audio_data.extend(chunk[:, 0])
            
            audio = np.array(audio_data[:samples_needed])
        else:
            # 新しいストリームを作成
            audio = sd.rec(int(duration * RECORDING_SAMPLE_RATE), 
                           samplerate=RECORDING_SAMPLE_RATE, 
                           channels=1, 
                           dtype='float32')
            sd.wait()
            audio = audio[:, 0]
    
    # 16kHzにリサンプリング
    audio_16k = librosa.resample(audio, 
                                  orig_sr=RECORDING_SAMPLE_RATE, 
                                  target_sr=TARGET_SAMPLE_RATE)
    
    # 保存
    sf.write(filename, audio_16k, TARGET_SAMPLE_RATE)
    
    if not use_vad:
        print(f"録音完了: {filename}")
    return filename


def speech_to_text_with_gemini(audio_path: str) -> str:
    """音声ファイルをGeminiでテキストに変換する
    
    Args:
        audio_path: 音声ファイルのパス
    
    Returns:
        str: 変換されたテキスト
        
    Raises:
        FileNotFoundError: 音声ファイルが見つからない場合
        RuntimeError: Gemini APIの呼び出しに失敗した場合
    """
    # 音声ファイルの存在確認
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"音声ファイルが見つかりません: {audio_path}")
    
    try:
        print("音声をテキストに変換中...")
        
        # Gemini APIで音声を処理
        audio_file = genai.upload_file(path=audio_path)
        response = model.generate_content([
            "この音声を正確に文字起こししてください。テキストのみを返してください。",
            audio_file
        ])
        
        text = response.text.strip()
        print(f"認識されたテキスト: {text}")
        
        # アップロードしたファイルを削除
        audio_file.delete()
        
        return text
    except Exception as e:
        print(f"エラー: 音声のテキスト変換に失敗しました: {e}")
        raise RuntimeError(f"音声のテキスト変換に失敗しました: {e}") from e


def take_photo_and_analyze_with_voice() -> None:
    """ウェイクワードを待機し、音声プロンプトで写真を撮影・分析する"""
    import lwake.features as features
    
    print("=" * 50)
    print("音声認識モードを開始します")
    print(f"ウェイクワードを言ってください...")
    print("=" * 50)
    
    # リファレンス音声を読み込む
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
    
    # 録音パラメータ
    buffer_duration = REFERENCE_AUDIO_LENGTH + 0.5
    slide_duration = 0.25
    
    buffer_samples = int(buffer_duration * RECORDING_SAMPLE_RATE)
    slide_samples = int(slide_duration * RECORDING_SAMPLE_RATE)
    
    audio_buffer = np.zeros(buffer_samples, dtype=np.float32)
    
    try:
        with sd.InputStream(samplerate=RECORDING_SAMPLE_RATE, channels=1, dtype=np.float32) as stream:
            while True:
                # 音声を読み取る
                data, overflowed = stream.read(slide_samples)
                
                chunk = data[:, 0]
                
                # バッファを更新
                audio_buffer = np.roll(audio_buffer, -len(chunk))
                audio_buffer[-len(chunk):] = chunk
                
                # 16kHzにリサンプリング
                audio_16k = librosa.resample(audio_buffer, 
                                             orig_sr=RECORDING_SAMPLE_RATE, 
                                             target_sr=TARGET_SAMPLE_RATE)
                
                # 特徴抽出
                try:
                    feat = features.extract_embedding_features(y=audio_16k, sample_rate=TARGET_SAMPLE_RATE)
                except Exception as e:
                    continue
                
                # リファレンスと比較
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
                
                # デバッグ: 最小距離を定期的に表示（10回に1回）
                if not detected and np.random.random() < 0.1:
                    print(f"  [デバッグ] 最小距離: {min_distance:.4f} ({best_match})", end='\r')
                
                if detected:
                    # 音声プロンプトを録音（既存のストリームを使用）
                    prompt_audio = record_voice_prompt(existing_stream=stream)
                    
                    # 音声をテキストに変換
                    prompt_text = speech_to_text_with_gemini(prompt_audio)
                    
                    # 写真を撮影
                    print("\n写真を撮影します...")
                    photo_path = take_photo()
                    
                    # Geminiで分析
                    result = analyze_photo_with_gemini(photo_path, prompt_text)
                    
                    # 結果を表示
                    print("\n" + "=" * 50)
                    print("Gemini AIの分析結果:")
                    print("=" * 50)
                    print(result)
                    print("=" * 50)
                    
                    # 録音ファイルを削除
                    os.remove(prompt_audio)
                    
                    # バッファをクリア
                    audio_buffer = np.zeros(buffer_samples, dtype=np.float32)
                    
                    print(f"\n再度ウェイクワードを言ってください...")
    
    except KeyboardInterrupt:
        print("\n\n音声認識を終了しました")
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

def take_multiple_photos(count: int = 3, interval: float = 2) -> List[str]:
    """複数枚の写真を連続撮影する
    
    Args:
        count: 撮影枚数
        interval: 撮影間隔（秒）
    
    Returns:
        list: 保存されたファイルのパスのリスト
        
    Raises:
        ValueError: countまたはintervalが無効な値の場合
    """
    # 入力値の検証
    if count <= 0:
        raise ValueError(f"countは正の整数である必要があります: {count}")
    if interval < 0:
        raise ValueError(f"intervalは0以上である必要があります: {interval}")
    
    # 保存ディレクトリを作成
    os.makedirs(PHOTO_DIR, exist_ok=True)
    
    photo_paths = []
    picam2 = Picamera2()
    
    try:
        camera_config = picam2.create_still_configuration()
        picam2.configure(camera_config)
        picam2.start()
        
        time.sleep(2)  # ウォームアップ
        
        for i in range(count):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"photo_{timestamp}_{i+1}.jpg"
            filepath = os.path.join(PHOTO_DIR, filename)
            picam2.capture_file(filepath)
            photo_paths.append(filepath)
            print(f"写真 {i+1}/{count} を保存しました: {filepath}")
            
            if i < count - 1:
                time.sleep(interval)
    finally:
        # リソースの確実なクリーンアップ
        picam2.stop()
        picam2.close()
    
    return photo_paths

def take_photo_with_metadata() -> str:
    """メタデータ付きで写真を撮影する
    
    Returns:
        str: 保存されたファイルのパス
        
    Raises:
        RuntimeError: カメラの初期化または撮影に失敗した場合
    """
    # 保存ディレクトリを作成
    os.makedirs(PHOTO_DIR, exist_ok=True)
    
    picam2 = Picamera2()
    
    try:
        # より詳細な設定
        config = picam2.create_still_configuration(
            main={"size": (1920, 1080)},  # 解像度の指定
            lores={"size": (640, 480)},    # 低解像度プレビュー
            display="lores"
        )
        picam2.configure(config)
        picam2.start()
        
        time.sleep(2)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"photo_{timestamp}.jpg"
        filepath = os.path.join(PHOTO_DIR, filename)
        
        # メタデータを取得して写真を撮影
        metadata = picam2.capture_metadata()
        picam2.capture_file(filepath)
        
        print(f"写真を保存しました: {filepath}")
        print(f"メタデータ: {metadata}")
        
        return filepath
    except Exception as e:
        print(f"エラー: 写真の撮影に失敗しました: {e}")
        raise RuntimeError(f"写真の撮影に失敗しました: {e}") from e
    finally:
        # リソースの確実なクリーンアップ
        picam2.stop()
        picam2.close()

if __name__ == "__main__":
    # デフォルトで音声認識モード
    take_photo_and_analyze_with_voice()
    
    # 以下は使用例（コメントアウト）
    # 基本的な使用例: 写真を撮影してAI分析
    # take_photo_and_analyze("この画像について詳しく説明してください。")
    
    # カスタムプロンプトの例
    # take_photo_and_analyze("この画像に写っているものを日本語でリストアップしてください。")
    
    # 写真のみ撮影する例
    # photo_path = take_photo()
    
    # 既存の写真を分析する例
    # result = analyze_photo_with_gemini("existing_photo.jpg", "この画像は何ですか？")
    # print(result)
    
    # 複数枚撮影の例
    # print("\n3枚の写真を連続撮影します...")
    # take_multiple_photos(count=3, interval=2)
    
    # メタデータ付き撮影の例
    # print("\nメタデータ付きで写真を撮影します...")
    # take_photo_with_metadata()
