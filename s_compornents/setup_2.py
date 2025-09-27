import os
import shutil
import openwakeword
import py7zr
import requests

openwakeword.utils.download_models()

def download_file(url, filename):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

def extract_and_rename(archive_path, output_dir, new_name):
    with py7zr.SevenZipFile(archive_path, mode='r') as archive:
        archive.extractall(path=output_dir)
    # 展開したディレクトリ名を取得してリネーム
    extracted_items = os.listdir(output_dir)
    for item in extracted_items:
        item_path = os.path.join(output_dir, item)
        if os.path.isdir(item_path) and item != new_name:
            new_path = os.path.join(output_dir, new_name)
            shutil.move(item_path, new_path)
            break

if __name__ == "__main__":
    url = "https://github.com/VOICEVOX/voicevox_engine/releases/download/0.24.1/voicevox_engine-linux-cpu-arm64-0.24.1.7z.001"
    archive_file = "voicevox_engine-linux-cpu-arm64-0.24.1.7z.001"
    output_directory = os.path.dirname(os.path.abspath(__file__))
    rename_to = "voicevox"
    archive_path = os.path.join(output_directory, archive_file)
    if not os.path.exists(archive_path):
        print("Downloading...")
        download_file(url, archive_path)
    extract_and_rename(archive_path, output_directory, rename_to)
    # 元ファイルを削除
    if os.path.exists(archive_path):
        os.remove(archive_path)