import vosk
import pyaudio
import json
import jaconv
import fugashi

class KatakanaTranscriber:
    def __init__(self, model_path, input_device_index=2, rate=16000, chunk=4000, frames_per_buffer=8000):
        self.tagger = fugashi.Tagger()
        self.model = vosk.Model(model_path)
        self.rec = vosk.KaldiRecognizer(self.model, rate)
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=rate,
            input=True,
            frames_per_buffer=frames_per_buffer,
            input_device_index=input_device_index
        )
        self.stream.start_stream()
        self.chunk = chunk

    def listen(self, on_transcribe):
        print("リアルタイム文字起こし開始(Ctrl+Cで終了)")
        try:
            while True:
                try:
                    data = self.stream.read(self.chunk, exception_on_overflow=False)
                except OSError:
                    continue  # オーバーフロー時はスキップ
                if self.rec.AcceptWaveform(data):
                    result = json.loads(self.rec.Result())
                    text = result.get("text", "")
                    for filler in ["えっと", "えーと"]:
                        text = text.replace(filler, "")
                    yomi = ""
                    for word in self.tagger(text):
                        yomi += getattr(word.feature, "katakana", word.surface)
                    zenkaku_text = jaconv.h2z(yomi, kana=True, digit=True, ascii=True)
                    on_transcribe(zenkaku_text)
        except KeyboardInterrupt:
            print("終了します")
        finally:
            if self.stream.is_active():
                self.stream.stop_stream()
            self.stream.close()
            self.p.terminate()

# 呼び出し例
if __name__ == "__main__":
    def print_katakana(text):
        print(text)

    transcriber = KatakanaTranscriber(
        model_path=r"s_compornents/compornents/model-ja",
        input_device_index=2
    )
    transcriber.listen(print_katakana)