# PiVot

ドーム型ロボット「PiVot」のメインプログラム

## 概要

PiVotは、Raspberry Piベースの音声対話型ロボットで、カメラによる視覚認識とサーボ制御による動作を組み合わせたシステムです。

## 主な機能

- **音声認識**: Whisperモデルによる日本語音声認識
- **視覚認識**: ov5647カメラとGemini-Robotics-ERによる高精度な画像解析
- **AI応答**: Gemini APIによる自然な会話
- **サーボ制御**: カメラの向き調整（水平・垂直）
- **QRコード表示**: URL情報の視覚化
- **音声合成**: AquesTalkPiによる日本語音声出力

## Gemini-Robotics-ER統合 🆕

Gemini-Robotics-ER (gemini-2.0-flash-exp) モデルを統合し、より詳細な視覚情報を取得できるようになりました。

### 処理フロー

1. カメラで写真撮影 (ov5647)
2. Robotics-ERモデルで画像を詳細解析（物体の位置、色、形状、空間的関係性）
3. 解析結果とユーザープロンプトを統合してメインGeminiに送信
4. Geminiの応答を処理（アクション実行 + 音声出力）

詳細は [ROBOTICS_ER_INTEGRATION.md](./ROBOTICS_ER_INTEGRATION.md) を参照してください。

## ドキュメント

- [ACTIONS.md](./ACTIONS.md) - AI応答とアクションのリンク機能
- [IMPLEMENTATION.md](./IMPLEMENTATION.md) - 実装の詳細
- [SERVO_INTEGRATION.md](./SERVO_INTEGRATION.md) - サーボ制御の統合
- [ROBOTICS_ER_INTEGRATION.md](./ROBOTICS_ER_INTEGRATION.md) - Robotics-ER統合の詳細

## セットアップ

```bash
# 依存関係のインストール
uv sync

# 環境変数の設定
cp .env.example .env
# .envファイルにGOOGLE_API_KEYを設定
```

## 実行

```bash
python3 main.py
```

HTTPサーバーが起動し、`http://pi.local:8100/clicked` にPOSTリクエストを送信すると音声認識が開始されます。

## テスト

```bash
# 既存機能のテスト
python3 test_minimal.py

# Robotics-ER統合のテスト
python3 test_robotics_integration.py

# Robotics-ERモデル単体のテスト（API呼び出しあり）
python3 test_robotics_er.py
```

