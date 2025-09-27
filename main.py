import subprocess
import os
from s_compornents.wakeword_detect_ext import WakewordDetector
from s_compornents.katakana_transcriber import KatakanaTranscriber
from s_compornents.voice import speak

def start_voicevox_engine():
    # run.shの絶対パスを取得
    run_sh_path = os.path.abspath("s_compornents/voicevox/linux-cpu/run.sh")
    # 実行権限を付与（Linuxのみ有効）
    subprocess.run(["chmod", "+x", run_sh_path])
    # VOICEVOXエンジン起動
    subprocess.Popen([run_sh_path])

def on_katakana_transcribed(text):
    print(f"音声認識結果（全角カタカナ）: {text}")
    speak(text)

def on_wakeword_detected():
    print("Wakewordが検出されました! 音声認識を開始します。")
    transcriber = KatakanaTranscriber(
        model_path=r"s_compornents/compornents/model-ja",
        input_device_index=2
    )
    transcriber.listen(on_katakana_transcribed)

if __name__ == "__main__":
    start_voicevox_engine()
    detector = WakewordDetector(
        model_path = r"s_compornents\compornents\taro_tsuu.onnx",
        inference_framework="onnx",
        chunk_size=1280,
        threshold=0.01,
        input_device_index=2,
        cooldown=1.0
    )
    detector.listen(on_wakeword_detected)