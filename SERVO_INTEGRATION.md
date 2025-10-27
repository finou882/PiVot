# PiVot AI応答と行動のリンク機能

## 概要

このドキュメントは、PiVotのAI応答とロボット行動をリンクさせる機能について説明します。

## 実装内容

### 1. 機能拡張ファイル: `servo_control.py`

サーボ制御とURL表示の機能を提供する拡張モジュールです。

#### 主な機能

##### `cam_move(shaft, angle)`
カメラ（サーボ）を指定した軸と角度に動かします。

**パラメータ:**
- `shaft` (str): 'x' または 'z'
  - 'x': 上下移動 (CH1)
  - 'z': 水平旋回 (CH0)
- `angle` (int/float): サーボの角度 (0-180度)

**例:**
```python
cam_move('z', 90)   # Z軸を90度（正面）に
cam_move('x', 180)  # X軸を180度（上向き）に
```

##### `url(url_string)`
指定されたURLのQRコードを表示します。

**パラメータ:**
- `url_string` (str): 表示するURL

**例:**
```python
url("https://www.google.com")
```

#### ハードウェア仕様
- **SparkFun Pi Servo Hat**
- CH0: Z軸（水平旋回: 0-180度）
- CH1: X軸（上下移動: 0-180度）
- 周波数: 50Hz
- 制御方式: I2C (アドレス 0x40) 経由でPWM制御
- PWM値: 209-623 (0-180度に対応、パルス幅 1.0ms-3.0ms)

### 2. AI応答パース機能

`main.py`に以下の機能を追加しました：

#### `parse_ai_response(response_text)`
AI応答からタグを抽出して分離します。

**戻り値:**
```python
{
    'response': str,  # ユーザーへの応答テキスト（<response>タグ内）
    'code': str,      # 実行するコード（<code>タグ内）
    'raw': str        # タグを除去した全文
}
```

#### `execute_ai_code(code_string)`
AI応答から抽出したコードを安全に実行します。

**セキュリティ:**
- `cam_move`と`url`関数のみ実行可能
- 組み込み関数は制限されています
- 不正なコードは実行されません

### 3. 統合フロー

1. **音声認識**: ユーザーの発話をWhisperで認識
2. **画像撮影**: カメラで現在の視界を撮影
3. **AI応答生成**: RAG.txtのプロンプトと画像を使用してGeminiが応答を生成
4. **応答パース**: 
   - `<response>タグ`内の応答テキストを抽出
   - `<code>タグ`内のコードを抽出
5. **コード実行**: 抽出したコードを安全に実行（サーボ制御など）
6. **音声出力**: 応答テキストをAquesTalkPiで音声出力

## AI応答フォーマット

RAG.txtで定義された形式に従って、AIは以下のようなタグ付き応答を返します：

### 例1: カメラ制御
```
<response>カメラヲミギニ20ド、スイヘイイドウサセマス。</response> <code>cam_move(shaft='z', angle=110)</code>
```

### 例2: 複合制御
```
<response>カメラヲミギウエスミヘイドウサセマス。</response> <code>cam_move(shaft='z', angle=150)
cam_move(shaft='x', angle=150)</code>
```

### 例3: URL表示
```
<response>GOOGLEノキューアールコードヲヒョウジシマス。</response> <code>url("https://www.google.com")</code>
```

### 例4: 情報提供のみ（コードなし）
```
<response>ソレハアオイコップデス。</response>
```

## テスト

`test_servo_integration.py`で以下のテストを実施：

1. **応答パーステスト**: タグの正しい抽出
2. **コード実行テスト**: サーボ制御とURL関数の実行
3. **セキュリティテスト**: 不正コードのブロック
4. **統合テスト**: エンドツーエンドの動作確認

## 依存関係

新たに追加された依存関係：
- `smbus2`: I2C通信でSparkFun Pi Servo Hat制御用
- `qrcode`: QRコード生成用

## セキュリティ

- コード実行は`cam_move`と`url`関数のみに制限
- `exec()`の実行環境は厳密に制御
- 組み込み関数へのアクセスは制限されています
- 不正なimportやシステムコマンドは実行できません

## 使用方法

1. システムを起動: `python3 main.py`
2. HTTPサーバーが`http://pi.local:8100`で起動
3. `/clicked`にPOSTリクエストを送信して音声認識を開始
4. ユーザーの発話に基づいてAIが応答し、必要に応じてサーボを制御

## 角度とPWM値の対応

SparkFun Pi Servo HatはI2C経由でPWM値を制御します。50HzのPWM信号で、サーボの制御パルス幅は以下の通りです：

| 角度 | PWM値 | パルス幅 |
|------|-------|---------|
| 0°   | 209   | 1.0ms   |
| 45°  | 312   | 1.5ms   |
| 90°  | 416   | 2.0ms   |
| 135° | 520   | 2.5ms   |
| 180° | 623   | 3.0ms   |

変換式: `pwm_value = int(209 + (angle / 180.0) * 414)`

この値は実際のハードウェアで動作確認されています。

## トラブルシューティング

### サーボが動かない場合
- SparkFun Pi Servo Hatが正しく接続されているか確認
- `smbus2`ライブラリがインストールされているか確認 (`pip install smbus2`)
- I2Cが有効になっているか確認 (`sudo raspi-config` -> Interface Options -> I2C)
- ハードウェアがない場合、シミュレーションモードで動作します

### QRコードが表示されない場合
- `qrcode`ライブラリがインストールされているか確認
- 画像表示ツール（feh）がインストールされているか確認
