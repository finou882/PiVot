#!/usr/bin/env python3
"""
音声サンプルを適切に処理してウェイクワード検出用に準備する
- 16kHzにリサンプリング
- 指定の長さに統一（末尾に無音をパディング）
"""

import soundfile as sf
import librosa
import numpy as np
import os
from pathlib import Path

# 設定
INPUT_DIR = "voice_examples"
OUTPUT_DIR = "voice_examples_16k"
TARGET_SAMPLE_RATE = 16000
TARGET_DURATION = 2.5  # 秒

def prepare_sample(input_file: str, output_file: str, target_sr: int = 16000, target_duration: float = 2.5) -> None:
    """音声サンプルを処理する
    
    Args:
        input_file: 入力音声ファイルのパス
        output_file: 出力音声ファイルのパス
        target_sr: 目標サンプルレート（Hz）
        target_duration: 目標の長さ（秒）
        
    Raises:
        FileNotFoundError: 入力ファイルが見つからない場合
        RuntimeError: 音声処理に失敗した場合
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"入力ファイルが見つかりません: {input_file}")
    
    try:
        # 読み込み＆リサンプリング
        audio, sr = librosa.load(input_file, sr=target_sr)
        
        # 目標のサンプル数
        target_samples = int(target_duration * target_sr)
        
        # 現在のサンプル数
        current_samples = len(audio)
        
        if current_samples < target_samples:
            # 短い場合：末尾に無音をパディング
            padding = target_samples - current_samples
            audio = np.pad(audio, (0, padding), mode='constant', constant_values=0)
            print(f"  パディング: {padding}サンプル ({padding/target_sr:.3f}秒) 追加")
        elif current_samples > target_samples:
            # 長い場合：カット（先頭から目標長まで）
            audio = audio[:target_samples]
            print(f"  カット: {current_samples - target_samples}サンプル ({(current_samples - target_samples)/target_sr:.3f}秒) 削除")
        
        # 保存
        sf.write(output_file, audio, target_sr)
        
        # 確認
        info = sf.info(output_file)
        print(f"  → {info.duration:.3f}秒, {info.samplerate}Hz")
    except Exception as e:
        raise RuntimeError(f"音声サンプルの処理に失敗しました: {e}") from e

def main() -> None:
    """メイン処理"""
    # 出力ディレクトリ作成
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print(f"音声サンプルを処理中...")
    print(f"  入力: {INPUT_DIR}/")
    print(f"  出力: {OUTPUT_DIR}/")
    print(f"  目標: {TARGET_DURATION}秒, {TARGET_SAMPLE_RATE}Hz")
    print()
    
    # 各サンプルを処理
    success_count = 0
    error_count = 0
    
    for i in range(1, 5):
        input_file = f"{INPUT_DIR}/Sample{i}.wav"
        output_file = f"{OUTPUT_DIR}/Sample{i}.wav"
        
        if not os.path.exists(input_file):
            print(f"Sample{i}.wav: ファイルが見つかりません - スキップ")
            error_count += 1
            continue
        
        try:
            # 元のファイル情報
            info = sf.info(input_file)
            print(f"Sample{i}.wav: {info.duration:.3f}秒, {info.samplerate}Hz")
            
            # 処理
            prepare_sample(input_file, output_file, TARGET_SAMPLE_RATE, TARGET_DURATION)
            success_count += 1
            print()
        except Exception as e:
            print(f"Sample{i}.wavの処理中にエラーが発生しました: {e}")
            error_count += 1
            print()
    
    print(f"完了！（成功: {success_count}, エラー: {error_count}）")
    print(f"\n使用方法:")
    print(f"  python main.py --voice")

if __name__ == "__main__":
    main()
