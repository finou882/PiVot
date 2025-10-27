"""
サーボ制御とアクション拡張モジュール
Pi Servo Hat を使用したサーボモーター制御機能を提供

CH0: Z軸 (水平旋回) - 左右の首振り
CH1: X軸 (上下移動) - 上下の首振り
PWM周波数: 50Hz
"""

import time
import subprocess
import os

try:
    from pi_servo_hat import PiServoHat
    PI_SERVO_HAT_AVAILABLE = True
except ImportError:
    PI_SERVO_HAT_AVAILABLE = False
    print("警告: pi_servo_hat ライブラリが見つかりません。サーボ制御はシミュレーションモードで動作します。")

# サーボハットの初期化
servo_hat = None
if PI_SERVO_HAT_AVAILABLE:
    try:
        servo_hat = PiServoHat()
        servo_hat.restart()
    except Exception as e:
        print(f"サーボハット初期化エラー: {e}")
        PI_SERVO_HAT_AVAILABLE = False

# サーボチャンネルマッピング
SERVO_CHANNEL_Z = 0  # Z軸（水平旋回）はCH0
SERVO_CHANNEL_X = 1  # X軸（上下移動）はCH1

# サーボの角度範囲（度）
SERVO_MIN_ANGLE = 0
SERVO_MAX_ANGLE = 180

# サーボのPWM設定（50Hz用）
# 一般的な50HzサーボのPWMデューティサイクル
# 0度 = 500μs (約2.5% duty), 90度 = 1500μs (約7.5% duty), 180度 = 2500μs (約12.5% duty)
SERVO_MIN_PULSE_WIDTH = 500   # マイクロ秒
SERVO_MAX_PULSE_WIDTH = 2500  # マイクロ秒
SERVO_FREQUENCY = 50  # Hz

def angle_to_pulse_width(angle):
    """
    角度をパルス幅（マイクロ秒）に変換
    
    Args:
        angle (int/float): サーボの角度 (0-180)
    
    Returns:
        int: パルス幅（マイクロ秒）
    """
    # 角度を0-180の範囲にクランプ
    angle = max(SERVO_MIN_ANGLE, min(SERVO_MAX_ANGLE, angle))
    
    # 線形補間でパルス幅を計算
    pulse_width = SERVO_MIN_PULSE_WIDTH + (angle / 180.0) * (SERVO_MAX_PULSE_WIDTH - SERVO_MIN_PULSE_WIDTH)
    return int(pulse_width)

def cam_move(shaft='z', angle=90):
    """
    カメラ（サーボ）を指定した軸と角度に移動
    
    Args:
        shaft (str): 'x' (上下) または 'z' (左右)
        angle (int/float): 目標角度 (0-180度)
    
    Example:
        cam_move(shaft='z', angle=90)  # Z軸を正面（90度）に
        cam_move(shaft='x', angle=180) # X軸を最大上向き（180度）に
    """
    shaft = shaft.lower()
    
    # 角度を0-180の範囲にクランプ
    angle = max(SERVO_MIN_ANGLE, min(SERVO_MAX_ANGLE, angle))
    
    # チャンネルを選択
    if shaft == 'z':
        channel = SERVO_CHANNEL_Z
        axis_name = "Z軸（水平）"
    elif shaft == 'x':
        channel = SERVO_CHANNEL_X
        axis_name = "X軸（上下）"
    else:
        print(f"エラー: 無効な軸指定 '{shaft}'. 'x' または 'z' を指定してください。")
        return
    
    # パルス幅を計算
    pulse_width = angle_to_pulse_width(angle)
    
    print(f"🎬 {axis_name} を {angle}度 に移動中... (CH{channel}, PWM: {pulse_width}μs)")
    
    if PI_SERVO_HAT_AVAILABLE and servo_hat:
        try:
            # サーボを動かす
            servo_hat.move_servo_position(channel, angle, 180)
            time.sleep(0.5)  # サーボの移動を待つ
            print(f"✅ {axis_name} を {angle}度 に移動完了")
        except Exception as e:
            print(f"サーボ制御エラー: {e}")
    else:
        # シミュレーションモード
        print(f"[シミュレーション] {axis_name} を {angle}度 に移動")
        time.sleep(0.3)

def url(url_string):
    """
    指定されたURLのQRコードを生成して表示
    
    Args:
        url_string (str): QRコード化するURL
    
    Example:
        url("https://www.google.com")
    """
    print(f"🔗 URLのQRコードを生成中: {url_string}")
    
    try:
        # QRコード生成用のPythonライブラリ (qrcode) を使用
        import qrcode
        
        # QRコードを生成
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url_string)
        qr.make(fit=True)
        
        # 画像を作成
        img = qr.make_image(fill_color="black", back_color="white")
        
        # QRコードを一時ファイルに保存
        qr_path = "/tmp/qrcode.png"
        img.save(qr_path)
        print(f"✅ QRコードを生成し、{qr_path} に保存しました")
        
        # 画像ビューアで表示（例: fbi, feh, display など）
        # Raspberry Pi の場合、fbi または feh を使用することが多い
        try:
            # fehを試す
            subprocess.run(['feh', '--fullscreen', qr_path], check=True, timeout=5)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            try:
                # displayを試す（ImageMagick）
                subprocess.run(['display', qr_path], check=True, timeout=5)
            except (FileNotFoundError, subprocess.TimeoutExpired):
                print(f"画像ビューアが見つかりません。QRコードは {qr_path} に保存されています。")
    
    except ImportError:
        print("エラー: qrcode ライブラリがインストールされていません。")
        print("インストールするには: pip install qrcode[pil]")
    except Exception as e:
        print(f"QRコード生成エラー: {e}")

# テスト用の関数
def test_servos():
    """サーボのテスト動作"""
    print("=== サーボテスト開始 ===")
    
    # Z軸テスト
    print("\n--- Z軸（水平）テスト ---")
    cam_move(shaft='z', angle=0)    # 左端
    time.sleep(1)
    cam_move(shaft='z', angle=90)   # 中央
    time.sleep(1)
    cam_move(shaft='z', angle=180)  # 右端
    time.sleep(1)
    cam_move(shaft='z', angle=90)   # 中央に戻す
    
    # X軸テスト
    print("\n--- X軸（上下）テスト ---")
    cam_move(shaft='x', angle=0)    # 下端
    time.sleep(1)
    cam_move(shaft='x', angle=90)   # 中央
    time.sleep(1)
    cam_move(shaft='x', angle=180)  # 上端
    time.sleep(1)
    cam_move(shaft='x', angle=90)   # 中央に戻す
    
    print("\n=== サーボテスト完了 ===")

if __name__ == "__main__":
    # モジュールを直接実行した場合のテスト
    print("サーボ制御モジュール - テストモード")
    test_servos()
