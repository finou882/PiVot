from s_compornents.wakeword_detect_ext import WakewordDetector

def on_wakeword_detected():
    print("Wakewordが検出されました!main.pyの処理が実行されます。")

detector = WakewordDetector(
    model_path = r"s_compornents\compornents\taro_tsuu.onnx",
    inference_framework="onnx",
    chunk_size=1280,
    threshold=0.01,
    input_device_index=2,
    cooldown=1.0
)
detector.listen(on_wakeword_detected)