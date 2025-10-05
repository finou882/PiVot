import os
import requests
import zipfile
import shutil

def download_file(url, filename):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

def extract_and_rename(zip_path, output_dir, new_name):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(output_dir)
    # 展開したディレクトリ名を取得してリネーム
    extracted_items = os.listdir(output_dir)
    for item in extracted_items:
        item_path = os.path.join(output_dir, item)
        if os.path.isdir(item_path) and item != new_name:
            new_path = os.path.join(output_dir, new_name)
            # 既存のmodel-jaがあれば削除
            if os.path.exists(new_path):
                shutil.rmtree(new_path)
            shutil.move(item_path, new_path)
            break

if __name__ == "__main__":
    url = "https://alphacephei.com/vosk/models/vosk-model-ja-0.22.zip"
    zip_file = "vosk-model-ja-0.22.zip"
    output_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "compornents")
    rename_to = "model-ja"
    zip_path = os.path.join(output_directory, zip_file)
    # compornentsフォルダがなければ作成
    os.makedirs(output_directory, exist_ok=True)
    if not os.path.exists(zip_path):
        print("Downloading...")
        download_file(url, zip_path)
    extract_and_rename(zip_path, output_directory, rename_to)
    # zipファイルを削除
    if os.path.exists(zip_path):
        os.remove(zip_path)