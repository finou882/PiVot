import subprocess
import os

# requirements.txtの絶対パスを取得
requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
subprocess.run(["pip", "install", "-r", requirements_path], check=True)
subprocess.run(["python", "-m", "setup_2.py"])