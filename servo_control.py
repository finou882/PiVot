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

# I2C通信でサーボハットを直接制御
try:
    import smbus
    I2C_AVAILABLE = True
    bus = smbus.SMBus(1)
    addr = 0x40
except ImportError:
    I2C_AVAILABLE = False
    print("警告: smbus ライブラリが見つかりません。サーボ制御はシミュレーションモードで動作します。")
except Exception as e:
    I2C_AVAILABLE = False
    print(f"I2Cバス初期化エラー: {e}")

# 従来のpi_servo_hatライブラリも試行
try:
    from pi_servo_hat import PiServoHat
    PI_SERVO_HAT_AVAILABLE = True
    servo_hat = None
except ImportError:
    PI_SERVO_HAT_AVAILABLE = False

# サーボハット初期化フラグ
servo_hat_initialized = False

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

def init_servo_hat():
    """サーボハットを初期化する"""
    global servo_hat_initialized
    if not I2C_AVAILABLE:
        print("I2Cが利用できません。初期化をスキップします。")
        return False
    
    try:
        bus.write_byte_data(addr, 0, 0x20)  # enables word writes
        time.sleep(.25)
        bus.write_byte_data(addr, 0, 0x10)  # enable Prescale change as noted in the datasheet
        time.sleep(.25)  # delay for reset
        bus.write_byte_data(addr, 0xfe, 0x79)  # changes the Prescale register value for 50 Hz
        bus.write_byte_data(addr, 0, 0x20)  # enables word writes
        time.sleep(.25)
        servo_hat_initialized = True
        print("✅ サーボハット初期化完了")
        return True
    except Exception as e:
        print(f"❌ サーボハット初期化エラー: {e}")
        return False

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

def angle_to_pwm(angle):
    """角度をPWM値に変換する（0-180度対応）"""
    # MG996Rサーボの仕様: 0度=150, 90度=331, 180度=512
    if angle < 0:
        angle = 0
    elif angle > 180:
        angle = 180
    
    # 線形補間で計算: PWM値 = 150 + (角度 * (512-150) / 180)
    pwm_value = int(150 + (angle * (512 - 150) / 180))
    return pwm_value

def move_servo_i2c(channel, angle):
    """
    I2C経由でサーボを指定した角度に移動する
    
    Args:
        channel (int): サーボチャンネル (0-15)
        angle (float): 目標角度 (0-180度)
    """
    global servo_hat_initialized
    
    if not I2C_AVAILABLE:
        return False
    
    # 初期化チェック
    if not servo_hat_initialized:
        if not init_servo_hat():
            return False
    
    if channel < 0 or channel > 15:
        print(f"エラー: チャンネル {channel} は無効です。0-15の範囲で指定してください。")
        return False
    
    try:
        pwm_value = angle_to_pwm(angle)
        
        # チャンネルに対応するレジスタアドレスを計算
        start_reg = 0x06 + (channel * 4)  # 開始時間レジスタ
        end_reg = 0x08 + (channel * 4)    # 終了時間レジスタ
        
        # PWM設定
        bus.write_word_data(addr, start_reg, 0)  # 開始時間 = 0us
        time.sleep(0.01)
        bus.write_word_data(addr, end_reg, pwm_value)  # 終了時間設定
        
        print(f"✅ チャンネル {channel}: {angle}度に移動 (PWM値: {pwm_value})")
        time.sleep(0.5)  # サーボの動作完了を待つ
        return True
    except Exception as e:
        print(f"❌ サーボ制御エラー (CH{channel}): {e}")
        return False

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
    
    print(f"🎬 {axis_name} を {angle}度 に移動中... (CH{channel})")
    
    # 方法1: I2C直接制御を試行
    if move_servo_i2c(channel, angle):
        print(f"✅ {axis_name} を {angle}度 に移動完了 (I2C制御)")
        return
    
    # 方法2: pi_servo_hatライブラリを試行
    if PI_SERVO_HAT_AVAILABLE:
        global servo_hat
        if not servo_hat:
            try:
                servo_hat = PiServoHat()
                servo_hat.restart()
            except Exception as e:
                print(f"pi_servo_hat初期化エラー: {e}")
                servo_hat = None
        
        if servo_hat:
            try:
                servo_hat.move_servo_position(channel, angle, 180)
                time.sleep(0.5)
                print(f"✅ {axis_name} を {angle}度 に移動完了 (pi_servo_hat)")
                return
            except Exception as e:
                print(f"pi_servo_hatエラー: {e}")
    
    # 方法3: シミュレーションモード
    print(f"[シミュレーション] {axis_name} を {angle}度 に移動")
    time.sleep(0.3)

def url(url_string):
    print("🔗 URLコマンド受信: 現在未実装 - URL:", url_string)

# 初期化とクリーンアップ関数
def init_gpio():
    """GPIO初期化 (I2Cサーボハット用)"""
    return init_servo_hat()

def cleanup_gpio():
    """GPIO クリーンアップ (将来の拡張用)"""
    global servo_hat_initialized
    servo_hat_initialized = False
    print("🔧 GPIO クリーンアップ完了")

# テスト用の関数
def test_servos():
    """サーボのテスト動作"""
    print("=== サーボテスト開始 ===")
    
    # 初期化
    print("🔧 サーボハット初期化中...")
    init_servo_hat()
    
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
