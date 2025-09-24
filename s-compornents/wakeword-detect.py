import pyaudio
import numpy as np
from openwakeword.model import Model

def listen_wakeword(model_path, inference_framework="onnx", chunk_size=1280, threshold=0.5):
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = chunk_size

    audio = pyaudio.PyAudio()
    mic_stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    # モデルパスを直接渡す（最新版仕様）
    owwModel = Model(wakeword_models=[model_path], inference_framework=inference_framework)
    model_name = list(owwModel.models.keys())[0]

    print(f"\nListening for wakeword: {model_name}\n")

    try:
        while True:
            audio_data = np.frombuffer(mic_stream.read(CHUNK), dtype=np.int16)
            prediction = owwModel.predict(audio_data)
            score = owwModel.prediction_buffer[model_name][-1]
            if score > threshold:
                print(f"Wakeword Detected! (score={score:.3f})")
            else:
                print(f"Listening... (score={score:.3f})", end='\r')
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        mic_stream.stop_stream()
        mic_stream.close()
        audio.terminate()

if __name__ == "__main__":
    listen_wakeword(
        model_path = r"C:\Users\finou\Projects\pivot\s-compornents\paibott_o.onnx",
        inference_framework="onnx",
        chunk_size=1280,
        threshold=0.5
    )