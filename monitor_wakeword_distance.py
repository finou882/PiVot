#!/usr/bin/env python3
"""
ウェイクワード検出の距離をリアルタイムで表示するデバッグツール
適切な閾値を見つけるために使用
"""

import sounddevice as sd
import librosa
import numpy as np
import os
import sys

# lwakeの特徴抽出をインポート
import lwake.features as features

# 設定
VOICE_EXAMPLES_DIR = "./voice_examples_16k"
RECORDING_SR = 48000
TARGET_SR = 16000
BUFFER_DURATION = 3.0  # 秒
SLIDE_DURATION = 0.25  # 秒

def main():
    print("=" * 60)
    print("ウェイクワード距離モニター")
    print("=" * 60)
    
    # リファレンス音声を読み込む
    print("\nリファレンス音声を読み込み中...")
    reference_features = []
    for i in range(1, 5):
        ref_path = f"{VOICE_EXAMPLES_DIR}/Sample{i}.wav"
        if os.path.exists(ref_path):
            feat = features.extract_embedding_features(path=ref_path)
            reference_features.append((f"Sample{i}.wav", feat))
            print(f"  ✓ {ref_path}")
    
    if not reference_features:
        print("エラー: リファレンス音声が見つかりません")
        return
    
    print(f"\n{len(reference_features)}個のリファレンス音声を読み込みました")
    print(f"バッファサイズ: {BUFFER_DURATION}秒")
    print(f"スライド間隔: {SLIDE_DURATION}秒")
    
    # 録音パラメータ
    buffer_samples = int(BUFFER_DURATION * RECORDING_SR)
    slide_samples = int(SLIDE_DURATION * RECORDING_SR)
    
    audio_buffer = np.zeros(buffer_samples, dtype=np.float32)
    
    print("\n" + "=" * 60)
    print("リアルタイム距離表示を開始します")
    print("ウェイクワードを言って、距離を確認してください")
    print("Ctrl+Cで終了")
    print("=" * 60)
    print()
    
    try:
        with sd.InputStream(samplerate=RECORDING_SR, channels=1, dtype=np.float32) as stream:
            while True:
                # 音声を読み取る
                data, overflowed = stream.read(slide_samples)
                if overflowed:
                    print("⚠ バッファオーバーフロー")
                
                chunk = data[:, 0]
                
                # バッファを更新
                audio_buffer = np.roll(audio_buffer, -len(chunk))
                audio_buffer[-len(chunk):] = chunk
                
                # 16kHzにリサンプリング
                audio_16k = librosa.resample(audio_buffer, 
                                             orig_sr=RECORDING_SR, 
                                             target_sr=TARGET_SR)
                
                # 特徴抽出
                try:
                    feat = features.extract_embedding_features(y=audio_16k, sample_rate=TARGET_SR)
                except Exception as e:
                    continue
                
                # 各リファレンスとの距離を計算
                distances = []
                for ref_name, ref_feat in reference_features:
                    distance = features.dtw_cosine_normalized_distance(feat, ref_feat)
                    distances.append((ref_name, distance))
                
                # 最小距離を表示
                distances.sort(key=lambda x: x[1])
                min_name, min_dist = distances[0]
                
                # プログレスバー風に表示
                bar_length = 40
                filled = int(min(min_dist * bar_length / 0.3, bar_length))
                bar = '█' * filled + '░' * (bar_length - filled)
                
                # 色分け（ANSI color codes）
                if min_dist < 0.05:
                    color = '\033[92m'  # 緑
                    status = "✓ 非常に近い"
                elif min_dist < 0.08:
                    color = '\033[93m'  # 黄色
                    status = "! 近い"
                elif min_dist < 0.15:
                    color = '\033[94m'  # 青
                    status = "- やや近い"
                else:
                    color = '\033[90m'  # グレー
                    status = "  遠い"
                
                reset = '\033[0m'
                
                # 1行で更新
                print(f"\r{color}{status}{reset} [{bar}] {min_dist:.4f} ({min_name})     ", end='', flush=True)
    
    except KeyboardInterrupt:
        print("\n\n終了しました")
        print("\n推奨閾値の目安:")
        print("  - 非常に厳格: 0.05")
        print("  - 厳格: 0.08")
        print("  - バランス: 0.10")
        print("  - 緩い: 0.15")

if __name__ == "__main__":
    # sounddeviceのデフォルト設定
    sd.default.samplerate = RECORDING_SR
    sd.default.channels = 1
    
    main()
