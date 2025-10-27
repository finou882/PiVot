"""
PiVot Servo Control Extension
サーボ制御とURL表示の機能を提供する拡張モジュール

使用するハードウェア: Pi Servo Hat
- CH0: Z軸 (水平旋回: 0-180度)
- CH1: X軸 (上下移動: 0-180度)
- 周波数: 50Hz
"""

import time
import subprocess
import webbrowser

# Pi Servo Hat制御用のライブラリをインポート
try:
    import RPi.GPIO as GPIO
    from adafruit_servokit import ServoKit
    SERVO_AVAILABLE = True
except ImportError:
    print("Warning: RPi.GPIO or adafruit_servokit not found. Servo control will be simulated.")
    SERVO_AVAILABLE = False

# サーボキットの初期化 (16チャンネル, 50Hz)
if SERVO_AVAILABLE:
    try:
        kit = ServoKit(channels=16, frequency=50)
        print("✅ ServoKit initialized (16 channels, 50Hz)")
    except Exception as e:
        print(f"⚠️ ServoKit initialization failed: {e}")
        SERVO_AVAILABLE = False

# チャンネル定義
CHANNEL_Z = 0  # Z軸（水平旋回）
CHANNEL_X = 1  # X軸（上下移動）

# 角度の範囲制限
MIN_ANGLE = 0
MAX_ANGLE = 180


def cam_move(shaft, angle):
    """
    カメラ（サーボ）を指定した軸と角度に動かす
    
    Parameters:
    -----------
    shaft : str
        'x' または 'z' - 制御する軸
        'x': 上下移動 (CH1)
        'z': 水平旋回 (CH0)
    angle : int or float
        サーボの角度 (0-180度)
    
    Returns:
    --------
    bool
        成功した場合True, 失敗した場合False
    
    Examples:
    ---------
    >>> cam_move('z', 90)  # Z軸を90度（正面）に
    >>> cam_move('x', 180)  # X軸を180度（上向き）に
    """
    # 入力検証
    if shaft not in ['x', 'z']:
        print(f"❌ Error: Invalid shaft '{shaft}'. Must be 'x' or 'z'.")
        return False
    
    # 角度を範囲内に制限
    angle = max(MIN_ANGLE, min(MAX_ANGLE, float(angle)))
    
    # チャンネル選択
    if shaft == 'z':
        channel = CHANNEL_Z
        axis_name = "Z軸（水平）"
    else:  # shaft == 'x'
        channel = CHANNEL_X
        axis_name = "X軸（上下）"
    
    print(f"🎯 カメラ移動: {axis_name} CH{channel} -> {angle}度")
    
    if SERVO_AVAILABLE:
        try:
            kit.servo[channel].angle = angle
            time.sleep(0.1)  # サーボの動作を待つ
            print(f"✅ サーボ移動完了: CH{channel} = {angle}度")
            return True
        except Exception as e:
            print(f"❌ サーボ制御エラー: {e}")
            return False
    else:
        # シミュレーションモード
        print(f"🔧 [SIMULATION] CH{channel} ({axis_name}) を {angle}度に設定")
        return True


def url(url_string):
    """
    指定されたURLのQRコードを表示する
    （実装方法はハードウェアに依存するため、ここでは基本的な処理を示す）
    
    Parameters:
    -----------
    url_string : str
        表示するURL
    
    Returns:
    --------
    bool
        成功した場合True, 失敗した場合False
    
    Examples:
    ---------
    >>> url("https://www.google.com")
    """
    print(f"🔗 URL表示: {url_string}")
    
    try:
        # QRコード生成（qrcodeライブラリを使用）
        try:
            import qrcode
            from PIL import Image
            
            # QRコードを生成
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(url_string)
            qr.make(fit=True)
            
            # 画像として保存
            img = qr.make_image(fill_color="black", back_color="white")
            qr_path = "/tmp/qrcode.png"
            img.save(qr_path)
            
            print(f"✅ QRコードを生成しました: {qr_path}")
            
            # 画像を表示（Raspberry Piのディスプレイに表示する場合）
            # fbiやfehなどのイメージビューアを使用
            try:
                subprocess.run(['feh', '--fullscreen', qr_path], check=False)
            except FileNotFoundError:
                print("⚠️ 画像表示ツール(feh)が見つかりません")
                # 代替: ブラウザでURLを開く
                try:
                    webbrowser.open(url_string)
                    print(f"✅ ブラウザでURLを開きました: {url_string}")
                except Exception as e:
                    print(f"⚠️ ブラウザを開けませんでした: {e}")
            
            return True
            
        except ImportError:
            print("⚠️ qrcodeライブラリが見つかりません")
            # QRコードが生成できない場合は、URLを表示するだけ
            print(f"📱 URL: {url_string}")
            return False
            
    except Exception as e:
        print(f"❌ URL処理エラー: {e}")
        return False


# テスト用のmain関数
if __name__ == "__main__":
    print("=== Servo Control Extension Test ===")
    
    # カメラ移動テスト
    print("\n[Test 1] Z軸を90度（正面）に")
    cam_move('z', 90)
    
    time.sleep(1)
    
    print("\n[Test 2] X軸を180度（上向き）に")
    cam_move('x', 180)
    
    time.sleep(1)
    
    print("\n[Test 3] Z軸を180度（右端）に")
    cam_move('z', 180)
    
    time.sleep(1)
    
    print("\n[Test 4] X軸を0度（下向き）に")
    cam_move('x', 0)
    
    time.sleep(1)
    
    print("\n[Test 5] 複合動作: 右上を見る")
    cam_move('z', 150)
    cam_move('x', 150)
    
    time.sleep(1)
    
    print("\n[Test 6] URL表示")
    url("https://www.google.com")
    
    print("\n=== Test Complete ===")
