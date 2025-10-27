"""
PiVot Servo Control Extension
サーボ制御とURL表示の機能を提供する拡張モジュール

使用するハードウェア: SparkFun Pi Servo Hat
- CH0: Z軸 (水平旋回: 0-180度)
- CH1: X軸 (上下移動: 0-180度)
- 周波数: 50Hz
- I2C通信でPWM制御
"""

import time
import subprocess
import webbrowser
import os

# SparkFun Pi Servo Hat制御用のライブラリをインポート (I2C通信)
try:
    import smbus2 as smbus
    SERVO_AVAILABLE = True
except ImportError:
    try:
        import smbus
        SERVO_AVAILABLE = True
    except ImportError:
        print("Warning: smbus/smbus2 not found. Servo control will be simulated.")
        SERVO_AVAILABLE = False

# QRコード生成用のライブラリをインポート
try:
    import qrcode
    from PIL import Image
    QRCODE_AVAILABLE = True
except ImportError:
    print("Warning: qrcode or PIL not found. QR code generation will be disabled.")
    QRCODE_AVAILABLE = False

# I2C設定
I2C_BUS = 1
SERVO_HAT_ADDR = 0x40

# サーボハットの初期化
if SERVO_AVAILABLE:
    try:
        bus = smbus.SMBus(I2C_BUS)
        # Initialize servo hat for 50Hz PWM
        bus.write_byte_data(SERVO_HAT_ADDR, 0, 0x20)  # enables word writes
        time.sleep(0.25)
        bus.write_byte_data(SERVO_HAT_ADDR, 0, 0x10)  # enable Prescale change
        time.sleep(0.25)
        bus.write_byte_data(SERVO_HAT_ADDR, 0xfe, 0x79)  # Prescale for 50 Hz
        bus.write_byte_data(SERVO_HAT_ADDR, 0, 0x20)  # enables word writes
        time.sleep(0.25)
        print("✅ SparkFun Pi Servo Hat initialized (50Hz via I2C)")
    except Exception as e:
        print(f"⚠️ Pi Servo Hat initialization failed: {e}")
        SERVO_AVAILABLE = False
        bus = None
else:
    bus = None

# チャンネル定義とレジスタアドレス
# CH0: レジスタ 0x06 (start), 0x08 (end)
# CH1: レジスタ 0x0A (start), 0x0C (end)
CHANNEL_REGISTERS = {
    0: {'start': 0x06, 'end': 0x08},  # Z軸（水平旋回）
    1: {'start': 0x0A, 'end': 0x0C},  # X軸（上下移動）
}

# 角度の範囲制限
MIN_ANGLE = 0
MAX_ANGLE = 180

# PWM値の範囲 (50Hzでの実測値に基づく)
# 0° = 209 (1.0ms), 90° = 416 (2.0ms), 180° = 623 (3.0ms)
MIN_PWM_VALUE = 209  # 1.0ms pulse width
MAX_PWM_VALUE = 623  # 3.0ms pulse width


def angle_to_pwm_value(angle):
    """
    角度（0-180度）をPWM値に変換
    
    50HzのPWM信号で、サーボの制御パルス幅は：
    - 0°: 1.0ms (PWM値 209)
    - 90°: 2.0ms (PWM値 416)
    - 180°: 3.0ms (PWM値 623)
    
    Parameters:
    -----------
    angle : float
        角度 (0-180度)
    
    Returns:
    --------
    int
        PWM値 (209-623)
    """
    # 0-180度を209-623にマッピング
    # 直線補間: pwm = 209 + (angle / 180) * (623 - 209)
    pwm_value = int(MIN_PWM_VALUE + (angle / 180.0) * (MAX_PWM_VALUE - MIN_PWM_VALUE))
    # 範囲内に制限
    return max(MIN_PWM_VALUE, min(MAX_PWM_VALUE, pwm_value))


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
    
    # 角度をPWM値に変換
    pwm_value = angle_to_pwm_value(angle)
    
    # チャンネル選択
    if shaft == 'z':
        channel = 0  # Z軸（水平旋回）
        axis_name = "Z軸（水平）"
    else:  # shaft == 'x'
        channel = 1  # X軸（上下移動）
        axis_name = "X軸（上下）"
    
    print(f"🎯 カメラ移動: {axis_name} CH{channel} -> {angle}度 (PWM値: {pwm_value})")
    
    if SERVO_AVAILABLE and bus is not None:
        try:
            # I2C経由でPWM値を書き込む
            regs = CHANNEL_REGISTERS[channel]
            
            # チャンネルの開始時間を0に設定
            bus.write_word_data(SERVO_HAT_ADDR, regs['start'], 0)
            time.sleep(0.05)
            
            # チャンネルの終了時間（PWM値）を設定
            bus.write_word_data(SERVO_HAT_ADDR, regs['end'], pwm_value)
            time.sleep(0.1)  # サーボの動作を待つ
            
            print(f"✅ サーボ移動完了: CH{channel} = {angle}度 (PWM値: {pwm_value})")
            return True
        except Exception as e:
            print(f"❌ サーボ制御エラー: {e}")
            return False
    else:
        # シミュレーションモード
        print(f"🔧 [SIMULATION] CH{channel} ({axis_name}) を {angle}度 (PWM値: {pwm_value}) に設定")
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
