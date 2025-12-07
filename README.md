# PiVot - Raspberry Pi Voice-Triggered Photo Analysis

Raspberry Pi用の音声起動型写真撮影・AI分析システム

## 概要

PiVotは、PiCamera2とGoogle Gemini AIを使用して、音声コマンドで写真を撮影し、AIによる画像分析を行うシステムです。ウェイクワード検出機能により、ハンズフリーで操作できます。

## 主な機能

- 🎤 音声ウェイクワード検出
- 📷 PiCamera2による写真撮影
- 🤖 Google Gemini AIによる画像分析
- 🔊 音声プロンプトによる質問
- 📝 RAG（Retrieval-Augmented Generation）プロンプト対応
- 🔄 連続撮影機能

## 必要な環境

- Python 3.13以上
- Raspberry Pi with カメラモジュール
- USBマイク
- Google Gemini API キー

## セットアップ

1. 依存関係のインストール：
```bash
uv sync
```

2. 環境変数の設定：
`.env`ファイルを作成し、以下を追加：
```
GEMINI_API_KEY=your_api_key_here
```

3. 音声サンプルの準備：
```bash
python prepare_voice_samples.py
```

## 使い方

### 基本的な使用方法

```bash
python main.py
```

ウェイクワードを言うと、音声プロンプトの録音が開始されます。質問を話した後、無音が続くと自動的に録音が停止し、写真を撮影してAI分析が行われます。

### デバッグツール

ウェイクワード検出の閾値を調整する場合：
```bash
python monitor_wakeword_distance.py
```

## 設定のカスタマイズ

`main.py`内の定数を変更することで、以下の設定をカスタマイズできます：

- `WAKE_THRESHOLD`: ウェイクワード検出の閾値
- `RECORDING_DURATION`: 最大録音時間
- `VAD_SILENCE_THRESHOLD`: 無音判定の閾値
- `PHOTO_DIR`: 写真の保存先ディレクトリ

## ライセンス

MIT License

## 作者

finou882
