import pyaudio
import numpy as np
import time
from openwakeword.model import Model

class WakewordDetector:
    def __init__(self, model_path, inference_framework="onnx", chunk_size=1280, threshold=0.01, input_device_index=2, cooldown=1.0):
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = chunk_size
        self.threshold = threshold
        self.cooldown = cooldown  # 検出後のクールダウン秒数
        self.last_detect_time = 0

        self.audio = pyaudio.PyAudio()
        self.mic_stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
            input_device_index=input_device_index
        )

        self.owwModel = Model(wakeword_models=[model_path], inference_framework=inference_framework)
        self.model_name = list(self.owwModel.models.keys())[0]

    def listen(self, on_detect):
        """
        on_detect: 検出時に呼び出す関数。引数なしで呼び出されます。
        """
        print(f"\nListening for wakeword: {self.model_name}\n")
        try:
            while True:
                audio_data = np.frombuffer(self.mic_stream.read(self.CHUNK), dtype=np.int16)
                prediction = self.owwModel.predict(audio_data)
                score = self.owwModel.prediction_buffer[self.model_name][-1]
                now = time.time()
                if score > self.threshold and (now - self.last_detect_time) > self.cooldown:
                    self.last_detect_time = now
                    print(f"Wakeword Detected! (score={score:.3f})")
                    on_detect()  # 呼び出し元の関数を実行
                else:
                    print(f"Listening... (score={score:.3f})", end='\r')
        except KeyboardInterrupt:
            print("\nStopped by user.")
        finally:
            self.mic_stream.stop_stream()
            self.mic_stream.close()
            self.audio.terminate()

# 呼び出し例
if __name__ == "__main__":
    def custom_action():
        print("Wakeword検出時に実行される関数です！")
        # ここに任意の処理を記述

    detector = WakewordDetector(
        model_path = r".\compornents\taro_tsuu.onnx",
        inference_framework="onnx",
        chunk_size=1280,
        threshold=0.01,
        input_device_index=2,
        cooldown=1.0
    )
    detector.listen(custom_action)