# Azure Document Intelligence OCR処理システム

群馬県政治資金PDFファイル電子化プロジェクトの一部として開発されたOCR処理システムです。Azure Document Intelligenceを使用して画像ファイルから文字を抽出し、CSV形式で出力します。

## 機能

- 複数の画像ファイル（PNG、JPG、JPEG、PDF）の一括OCR処理
- 複数の様式に対応（様式ごとに異なる学習済みモデルを使用）
- エラーハンドリングとログ出力
- CSV形式での結果出力

## 必要条件

- Python 3.8以上
- Azure Document Intelligenceのアカウントとカスタムモデル
- Windows/Linux/macOS環境

## インストール

1. リポジトリのクローン
```bash
git clone <repository-url>
cd SOL-260
```

2. 依存関係のインストール
```bash
pip install -r requirements.txt
```

3. 環境変数の設定
```bash
cp .env.example .env
```

`.env`ファイルを編集し、以下の情報を設定してください：
```
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-resource-name.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=your-api-key-here
MODEL_ID_FORM_6_5=your-model-id-for-form-6-5
MODEL_ID_FORM_6_2_5=your-model-id-for-form-6-2-5
MODEL_ID_FORM_7_5=your-model-id-for-form-7-5
MODEL_ID_FORM_7_3_5=your-model-id-for-form-7-3-5
```

## 使用方法

### コマンドライン実行

```bash
python main.py <入力フォルダパス> <様式タイプ> [オプション]
```

#### 引数

- `input_folder`: 処理する画像ファイルが含まれるフォルダのパス
- `form_type`: 処理する様式タイプ（6-5、6-2-5、7-5、7-3-5）

#### オプション

- `-o, --output`: 出力CSVファイルのパス（デフォルト: output.csv）
- `-c, --config`: 設定ファイルのパス（JSON形式）
- `-v, --verbose`: 詳細なログ出力を有効にする

#### 実行例

```bash
# 基本的な使用
python main.py ./images 6-5

# 出力ファイルを指定
python main.py ./images 6-2-5 -o result.csv

# 設定ファイルを使用
python main.py ./images 7-5 -c config.json

# 詳細ログ付き
python main.py ./images 7-3-5 -v
```

### 設定ファイル

様式とモデルIDのマッピングを設定ファイルで管理できます：

`config.json`の例：
```json
{
    "model_mapping": {
        "6-5": "model-id-1",
        "6-2-5": "model-id-2",
        "7-5": "model-id-3",
        "7-3-5": "model-id-4"
    }
}
```

## 出力形式

CSVファイルは以下の列を含みます：

| 列名 | 説明 |
|------|------|
| filename | 処理した画像ファイル名 |
| page | ページ番号 |
| ocr_result | OCRで抽出されたテキスト |

## 開発

### テストの実行

```bash
# 全テストを実行
pytest

# カバレッジ付きでテストを実行
pytest --cov=src tests/

# 特定のテストのみ実行
pytest tests/test_ocr_processor.py -v
```

### プロジェクト構造

```
SOL-260/
├── src/
│   ├── __init__.py
│   ├── ocr_processor.py    # メインのOCR処理クラス
│   ├── config.py           # 設定管理
│   └── utils.py            # ユーティリティ関数
├── tests/
│   ├── __init__.py
│   ├── test_ocr_processor.py
│   └── test_batch_processor.py
├── docs/
│   └── design/             # 設計ドキュメント
├── main.py                 # エントリーポイント
├── requirements.txt        # Python依存関係
├── pytest.ini             # pytest設定
├── .env.example           # 環境変数テンプレート
└── README.md              # このファイル
```

## トラブルシューティング

### エラー: "Azure Document Intelligenceのエンドポイントとキーが設定されていません"

`.env`ファイルが正しく設定されているか確認してください。

### エラー: "未定義の様式です"

指定した様式が設定に含まれているか確認してください。利用可能な様式はエラーメッセージに表示されます。

### OCR処理が失敗する

- 画像ファイルが破損していないか確認
- Azure Document Intelligenceのモデルが正しくトレーニングされているか確認
- ログファイルで詳細なエラーメッセージを確認

## ライセンス

このプロジェクトは内部使用のみを目的としています。

## 設計ドキュメント

詳細な設計情報は `/docs/design/` フォルダ内の設計ドキュメントを参照してください。