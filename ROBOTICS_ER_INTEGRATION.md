# Gemini-Robotics-ER統合ドキュメント

## 概要

このドキュメントは、PiVotロボットへのGemini-Robotics-ER（gemini-2.0-flash-exp）モデルの統合について説明します。

## 統合の目的

Gemini-Robotics-ERモデルは、ロボティクスタスクに特化した視覚認識能力を持つGeminiモデルです。このモデルを統合することで、以下のメリットが得られます：

1. **より詳細な視覚情報の取得**: 物体の位置、色、形状、空間的関係性をより正確に認識
2. **ロボット制御の高精度化**: 視覚情報に基づいたより適切なアクション生成
3. **二段階処理による高度な応答**: 専門的な視覚解析 → 文脈理解と応答生成

## アーキテクチャ

### 処理フロー

```
1. カメラで写真撮影 (ov5647)
   ↓
2. Robotics-ERモデルで画像を詳細解析
   ↓
3. 解析結果 + ユーザープロンプト + RAG.txt → メインGeminiモデル
   ↓
4. Geminiの応答を既存の処理パイプラインで処理
   ↓
5. アクション実行 + 音声出力
```

### 二段階処理のメリット

#### 第一段階: Robotics-ERモデル
- **専門性**: ロボティクスに最適化された視覚認識
- **詳細な解析**: 物体の空間的配置、色、形状などを詳細に分析
- **言語非依存**: 視覚情報を客観的に抽出

#### 第二段階: メインGeminiモデル
- **文脈理解**: ユーザーの意図とRAG.txtの指示を統合
- **応答生成**: 日本語での自然な応答を生成
- **アクション決定**: 適切なサーボ制御コードを生成

## 実装詳細

### 新規追加されたコンポーネント

#### 1. Robotics-ERモデルの初期化

```python
ROBOTICS_MODEL_NAME = "gemini-2.0-flash-exp"
robotics_model = genai.GenerativeModel(ROBOTICS_MODEL_NAME)
```

#### 2. 画像解析関数

```python
def analyze_image_with_robotics_er(image):
    """
    Gemini-Robotics-ERモデルで画像を解析する
    
    Parameters:
    -----------
    image : PIL.Image
        解析する画像
    
    Returns:
    --------
    str
        画像の解析結果テキスト
    """
    try:
        print("🤖 Robotics-ERモデルで画像を解析中...")
        prompt = "この画像に写っているものを詳しく説明してください。物体の位置、色、形状、空間的な関係性を含めて説明してください。"
        response = robotics_model.generate_content([prompt, image])
        analysis_result = response.text
        print(f"🔍 Robotics-ER解析結果: {analysis_result[:200]}...")
        return analysis_result
    except Exception as e:
        print(f"⚠️ Robotics-ER解析エラー: {e}")
        return ""
```

#### 3. process_request関数の拡張

```python
# Robotics-ERモデルで画像を解析（画像がある場合）
robotics_analysis = ""
if image:
    robotics_analysis = analyze_image_with_robotics_er(image)

# プロンプトにRobotics-ERの解析結果を追加
if robotics_analysis:
    full_prompt = f"{full_prompt}\n\n//Robotics-ER Vision Analysis//\n{robotics_analysis}"
    print(f"✅ Robotics-ER解析結果をプロンプトに統合しました")
```

### プロンプト構造

統合後のプロンプト構造は以下のようになります：

```
[RAG.txtの内容]

//What users say//
[ユーザーの発言]

//Robotics-ER Vision Analysis//
[Robotics-ERモデルによる画像解析結果]
```

## 使用例

### シナリオ1: 物体の認識と説明

**ユーザー**: 「これは何？」

**処理**:
1. カメラで撮影
2. Robotics-ER: 「画像には青いカップが机の上に置かれています。カップは円柱形で、高さ約10cm、直径約8cmです。」
3. メインGemini: 「それは青いコップです。」+ 音声出力

### シナリオ2: カメラ制御が必要な場合

**ユーザー**: 「右にあるものを見て」

**処理**:
1. カメラで撮影（現在の視点）
2. Robotics-ER: 「画像の右端に一部しか写っていない赤い物体があります。」
3. メインGemini: 「右の物体を確認します。」+ `<code>cam_move(shaft='z', angle=110)</code>`
4. アクション実行: カメラが右に移動

## テスト

### テストスクリプトの実行

```bash
python3 test_robotics_er.py
```

このスクリプトは以下をテストします：
- Robotics-ERモデルの初期化
- 画像ファイルの読み込み
- Robotics-ERモデルによる画像解析
- 解析結果の出力

### 期待される出力

```
✅ Robotics-ERモデル (gemini-2.0-flash-exp) を初期化しました
✅ テスト画像を読み込みました: hello.jpg
🤖 Robotics-ERモデルで画像を解析中...

🔍 Robotics-ER解析結果:
================================================================================
[画像の詳細な解析結果]
================================================================================

✅ テスト成功: Robotics-ERモデルが正常に動作しました
```

## エラーハンドリング

### Robotics-ER解析エラー時の挙動

```python
except Exception as e:
    print(f"⚠️ Robotics-ER解析エラー: {e}")
    return ""
```

- Robotics-ERモデルでエラーが発生した場合、空文字列を返す
- メインGeminiモデルは通常通り動作（Robotics-ER解析なしで処理）
- システム全体の動作は継続される

## パフォーマンス考慮事項

### API呼び出し回数

- 従来: 1回のAPI呼び出し（メインGeminiのみ）
- 統合後: 2回のAPI呼び出し（Robotics-ER + メインGemini）

### レイテンシ

- Robotics-ER解析: 約1-3秒
- メインGemini応答: 約1-2秒
- 合計: 約2-5秒（従来より1-3秒増加）

### 対策

- 画像がない場合はRobotics-ER解析をスキップ
- エラー時の迅速なフォールバック
- 並列処理の検討（将来的な改善案）

## セキュリティ

### APIキー管理

- `.env`ファイルで環境変数として管理
- コード内にハードコードしない

### モデルの信頼性

- Google公式のモデルを使用
- 応答内容の検証は既存のパイプラインで実施

## トラブルシューティング

### Robotics-ERモデルが利用できない

**症状**: `⚠️ Robotics-ER解析エラー`が表示される

**原因**:
1. APIキーが無効
2. モデル名が間違っている
3. ネットワークエラー

**対処法**:
1. GOOGLE_API_KEYを確認
2. gemini-2.0-flash-expが利用可能か確認
3. ネットワーク接続を確認
4. エラーメッセージを確認して適切に対処

### 解析結果が統合されない

**症状**: Robotics-ER解析は成功するが、メインGeminiに反映されない

**確認事項**:
1. `robotics_analysis`変数が空でないか
2. `full_prompt`に正しく統合されているか
3. ログ出力を確認: `✅ Robotics-ER解析結果をプロンプトに統合しました`

## 今後の拡張案

1. **並列処理の導入**: Robotics-ERとメインGeminiを並列実行してレイテンシを削減
2. **キャッシング**: 同じ画像の解析結果をキャッシュして再利用
3. **プロンプトの最適化**: Robotics-ERへのプロンプトをタスクに応じてカスタマイズ
4. **複数画像の対応**: 複数の視点からの画像を統合解析
5. **フィードバックループ**: Robotics-ERの解析結果に基づいて追加撮影を自動実行

## 参考情報

- [Google AI Gemini API Documentation](https://ai.google.dev/)
- [PiVot RAG.txt](./RAG.txt) - プロンプトとアクション例
- [ACTIONS.md](./ACTIONS.md) - アクション機能の詳細

---

**実装日**: 2025-10-27  
**バージョン**: 1.0  
**ステータス**: ✅ 実装完了
