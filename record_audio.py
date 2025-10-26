#!/usr/bin/env python3
"""
マイク録音してMP3形式で保存するスクリプト
使用方法: python record_audio.py [録音時間（秒）] [出力ファイル名]
例: python record_audio.py 10 my_recording.mp3
"""

import sys
import time
import wave
import pyaudio
import numpy as np
from pydub import AudioSegment
from datetime import datetime
import os

# 録音設定
SAMPLE_RATE = 44100
CHUNK_SIZE = 1024
CHANNELS = 1
FORMAT = pyaudio.paInt16
MICROPHONE_INDEX = 1  # main.pyと同じマイク設定

def record_audio(duration=10, output_filename=None):
    """
    マイクから音声を録音してMP3で保存
    
    Args:
        duration (int): 録音時間（秒）
        output_filename (str): 出力ファイル名（.mp3）
    """
    
    if output_filename is None:
        # タイムスタンプ付きのファイル名を自動生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"recording_{timestamp}.mp3"
    
    # .mp3拡張子を確実に付ける
    if not output_filename.endswith('.mp3'):
        output_filename += '.mp3'
    
    print(f"🎤 録音開始... {duration}秒間録音します")
    print(f"📁 保存先: {output_filename}")
    
    # PyAudio初期化
    p = pyaudio.PyAudio()
    
    try:
        # マイクストリーム開始
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE,
            input_device_index=MICROPHONE_INDEX
        )
        
        print("🔴 録音中...")
        
        frames = []
        total_frames = int(SAMPLE_RATE / CHUNK_SIZE * duration)
        
        for i in range(total_frames):
            try:
                data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                frames.append(data)
                
                # プログレス表示
                progress = (i + 1) / total_frames * 100
                if i % (total_frames // 10) == 0:  # 10%刻みで表示
                    print(f"進行状況: {progress:.0f}%")
                    
            except Exception as e:
                print(f"録音エラー: {e}")
                break
        
        print("⏹️ 録音完了")
        
        # ストリーム停止
        stream.stop_stream()
        stream.close()
        
        # WAVファイルとして一時保存
        temp_wav = "temp_recording.wav"
        with wave.open(temp_wav, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(b''.join(frames))
        
        print("🔄 MP3に変換中...")
        
        # WAVからMP3に変換
        audio = AudioSegment.from_wav(temp_wav)
        audio.export(output_filename, format="mp3", bitrate="192k")
        
        # 一時ファイル削除
        os.remove(temp_wav)
        
        # ファイル情報表示
        file_size = os.path.getsize(output_filename)
        print(f"✅ 録音完了！")
        print(f"📄 ファイル: {output_filename}")
        print(f"📊 サイズ: {file_size / 1024:.1f} KB")
        print(f"⏱️ 録音時間: {duration}秒")
        
        return output_filename
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return None
        
    finally:
        p.terminate()

def list_audio_devices():
    """利用可能なオーディオデバイスを一覧表示"""
    p = pyaudio.PyAudio()
    print("\n🎧 利用可能なオーディオデバイス:")
    print("-" * 50)
    
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        if device_info['maxInputChannels'] > 0:  # 入力デバイスのみ
            print(f"ID {i}: {device_info['name']}")
            print(f"   チャンネル数: {device_info['maxInputChannels']}")
            print(f"   サンプルレート: {device_info['defaultSampleRate']}")
            print()
    
    p.terminate()

def main():
    """メイン関数"""
    if len(sys.argv) > 1 and sys.argv[1] == "--list-devices":
        list_audio_devices()
        return
    
    # コマンドライン引数の解析
    duration = 10  # デフォルト10秒
    output_filename = None
    
    if len(sys.argv) > 1:
        try:
            duration = int(sys.argv[1])
        except ValueError:
            print("❌ 録音時間は整数で指定してください")
            sys.exit(1)
    
    if len(sys.argv) > 2:
        output_filename = sys.argv[2]
    
    print("=" * 50)
    print("🎤 マイク録音スクリプト")
    print("=" * 50)
    print(f"録音時間: {duration}秒")
    print("準備完了。3秒後に録音開始...")
    
    # カウントダウン
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    # 録音実行
    result = record_audio(duration, output_filename)
    
    if result:
        print(f"\n🎉 録音が正常に完了しました！")
        print(f"ファイル: {result}")
    else:
        print(f"\n❌ 録音に失敗しました")
        sys.exit(1)

if __name__ == "__main__":
    main()