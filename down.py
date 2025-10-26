import pyaudio
p = pyaudio.PyAudio()
info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')
print("--- 入力デバイスリスト ---")
for i in range(0, numdevices):
    dev_info = p.get_device_info_by_host_api_device_index(0, i)
    # 入力チャンネルがあるデバイスのみ表示
    if dev_info.get('maxInputChannels') > 0:
        print(f"Index {i}: {dev_info.get('name')} (Channels: {dev_info.get('maxInputChannels')})")
p.terminate()