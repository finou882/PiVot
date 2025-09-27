import requests
import sounddevice as sd
import numpy as np

VOICEVOX_ENGINE_URL = "http://localhost:50021"
SPEAKER_ID = 11  # 好きな話者IDに変更

def speak(text, speaker=SPEAKER_ID):
    # クエリ作成
    query_payload = {
        "text": text,
        "speaker": speaker,
        "enable_katakana_english": True
    }
    r = requests.post(f"{VOICEVOX_ENGINE_URL}/audio_query", params=query_payload)
    r.raise_for_status()
    query = r.json()

    # 音声合成
    synth_payload = {
        "speaker": speaker,
        "enable_interrogative_upspeak": True
    }
    r = requests.post(f"{VOICEVOX_ENGINE_URL}/synthesis", params=synth_payload, json=query)
    r.raise_for_status()
    wav_bytes = r.content

    # WAV再生
    import io
    import wave
    with wave.open(io.BytesIO(wav_bytes), 'rb') as wf:
        rate = wf.getframerate()
        channels = wf.getnchannels()
        frames = wf.readframes(wf.getnframes())
        audio = np.frombuffer(frames, dtype=np.int16)
        if channels == 2:
            audio = audio.reshape(-1, 2)
        sd.play(audio, rate)
        sd.wait()