"""
PiVot Servo Control Extension
サーボ制御とURL表示の機能を提供する拡張モジュール

使用するハードウェア: SparkFun Pi Servo Hat
- CH0: Z軸 (水平旋回: 0-180度 -> 1-512値)
- CH1: X軸 (上下移動: 0-180度 -> 1-512値)
- 周波数: 50Hz
"""

import time
import subprocess
import webbrowser
import os

# SparkFun Pi Servo Hat制御用のライブラリをインポート
try:
    import pi_servo_hat
    SERVO_AVAILABLE = True
except ImportError:
    print("Warning: pi_servo_hat not found. Servo control will be simulated.")
    SERVO_AVAILABLE = False

# QRコード生成用のライブラリをインポート
try:
    import qrcode
    from PIL import Image
    QRCODE_AVAILABLE = True
except ImportError:
    print("Warning: qrcode or PIL not found. QR code generation will be disabled.")
    QRCODE_AVAILABLE = False

# サーボハットの初期化
if SERVO_AVAILABLE:
    try:
        # Initialize the servo hat library
        pi_servo_hat.restart()
        print("✅ SparkFun Pi Servo Hat initialized")
    except Exception as e:
        print(f"⚠️ Pi Servo Hat initialization failed: {e}")
        SERVO_AVAILABLE = False

# チャンネル定義
CHANNEL_Z = 0  # Z軸（水平旋回）
CHANNEL_X = 1  # X軸（上下移動）

# 角度の範囲制限
MIN_ANGLE = 0
MAX_ANGLE = 180

# サーボ値の範囲 (SparkFun Pi Servo Hat: 1-512)
MIN_SERVO_VALUE = 1
MAX_SERVO_VALUE = 512


def angle_to_servo_value(angle):
    """
    角度（0-180度）をサーボ値（1-512）に変換
    
    Parameters:
    -----------
    angle : float
        角度 (0-180度)
    
    Returns:
    --------
    int
        サーボ値 (1-512)
    """
    # 0-180度を1-512にマッピング
    servo_value = int(((angle / 180.0) * 511) + 1)
    # 範囲内に制限
    return max(MIN_SERVO_VALUE, min(MAX_SERVO_VALUE, servo_value))


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
    
    # 角度をサーボ値に変換
    servo_value = angle_to_servo_value(angle)
    
    # チャンネル選択
    if shaft == 'z':
        channel = CHANNEL_Z
        axis_name = "Z軸（水平）"
    else:  # shaft == 'x'
        channel = CHANNEL_X
        axis_name = "X軸（上下）"
    
    print(f"🎯 カメラ移動: {axis_name} CH{channel} -> {angle}度 (サーボ値: {servo_value})")
    
    if SERVO_AVAILABLE:
        try:
            # SparkFun Pi Servo Hatのmove_servo_position関数を使用
            # move_servo_position(channel, position)
            # channel: 0-15, position: 1-512
            pi_servo_hat.move_servo_position(channel, servo_value)
            time.sleep(0.1)  # サーボの動作を待つ
            print(f"✅ サーボ移動完了: CH{channel} = {angle}度 (値: {servo_value})")
            return True
        except Exception as e:
            print(f"❌ サーボ制御エラー: {e}")
            return False
    else:
        # シミュレーションモード
        print(f"🔧 [SIMULATION] CH{channel} ({axis_name}) を {angle}度 (値: {servo_value}) に設定")
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
        if QRCODE_AVAILABLE:
            # QRコードを生成
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(url_string)
            qr.make(fit=True)
            
            # 画像として保存（セキュアなパスを使用）
            img = qr.make_image(fill_color="black", back_color="white")
            qr_path = "/tmp/qrcode.png"
            
            # パスの検証（セキュリティ対策）
            qr_path = os.path.abspath(qr_path)
            if not qr_path.startswith("/tmp/"):
                raise ValueError("Invalid file path")
            
            img.save(qr_path)
            
            print(f"✅ QRコードを生成しました: {qr_path}")
            
            # 画像を表示（Raspberry Piのディスプレイに表示する場合）
            # fbiやfehなどのイメージビューアを使用
            try:
                # セキュリティ: パスを検証してからsubprocessを実行
                if os.path.exists(qr_path) and qr_path.startswith("/tmp/"):
                    subprocess.run(['feh', '--fullscreen', qr_path], check=False, timeout=5)
            except FileNotFoundError:
                print("⚠️ 画像表示ツール(feh)が見つかりません")
                # 代替: ブラウザでURLを開く
                try:
                    webbrowser.open(url_string)
                    print(f"✅ ブラウザでURLを開きました: {url_string}")
                except Exception as e:
                    print(f"⚠️ ブラウザを開けませんでした: {e}")
            except subprocess.TimeoutExpired:
                print("⚠️ 画像表示がタイムアウトしました")
            
            return True
            
        else:
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
