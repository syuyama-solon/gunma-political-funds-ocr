# AI評価モードの使用方法

政治資金収支報告書のOCR処理において、AI評価列の出力を制御できる4つのモードを提供しています。

## AI評価モードオプション

### 1. モード1: すべてのAI列を出力（デフォルト）
```bash
python main.py ./images 6-5 -o output.tsv --ai-mode 1
# または --ai-mode を省略（デフォルトが1）
python main.py ./images 6-5 -o output.tsv
```

出力されるAI列：
- AI__payee_name（支出先名）
- AI__payee_address（支出先住所）
- AI__payment_date_extracted（支出日）
- AI__payment_purpose（支払い用途）
- AI__validity_score（妥当性スコア）
- AI__validity_reason（妥当性評価の理由）
- AI__transparency_score（透明性スコア）
- AI__alternative_suggestion（代替案提案）
- AI__news_value_potential_score（ニュース価値スコア）
- AI__news_value_potential_score_reason（ニュース価値の理由）
- AI__business_type（業種）
- AI__website（ウェブサイト）
- AI__payee_detail（支出先詳細）

### 2. モード2: すべてのAI列を出力しない
```bash
python main.py ./images 6-5 -o output.tsv --ai-mode 2
```

AI分析は実行されますが、結果は出力ファイルに含まれません。

### 3. モード3: 特定のAI列のみ除外
```bash
# payee_detailとwebsiteを除外して他のAI列は出力
python main.py ./images 6-5 -o output.tsv --ai-mode 3 --ai-columns payee_detail website

# news関連の列を除外
python main.py ./images 6-5 -o output.tsv --ai-mode 3 --ai-columns news_value_potential_score news_value_potential_score_reason
```

### 4. モード4: 特定のAI列のみ出力
```bash
# 妥当性評価とニュース価値のみ出力
python main.py ./images 6-5 -o output.tsv --ai-mode 4 --ai-columns validity_score validity_reason news_value_potential_score

# 基本情報のみ出力
python main.py ./images 6-5 -o output.tsv --ai-mode 4 --ai-columns payee_name payment_date_extracted payment_purpose
```

## 使用例

### 例1: 完全なAI分析を実行
```bash
python main.py ./receipts 7-5 -o full_analysis.tsv
```

### 例2: AI分析なしでOCRのみ実行
```bash
python main.py ./receipts 7-5 -o ocr_only.tsv --ai-mode 2
```

### 例3: 重要な評価項目のみ出力
```bash
python main.py ./receipts 7-5 -o key_metrics.tsv --ai-mode 4 --ai-columns validity_score validity_reason transparency_score news_value_potential_score
```

### 例4: 詳細情報を除外してコンパクトな出力
```bash
python main.py ./receipts 7-5 -o compact.tsv --ai-mode 3 --ai-columns payee_detail business_type website
```

## 注意事項

- `--ai-columns`オプションは`--ai-mode 3`または`--ai-mode 4`と組み合わせて使用します
- AI列名は`AI__`プレフィックスなしで指定します（例: `payee_name`であり、`AI__payee_name`ではない）
- OpenAI APIキーが設定されていない場合、AI分析は実行されません
- `--no-analyze-receipts`オプションを使用すると、AI分析自体が無効になります

## パフォーマンスの考慮事項

- モード2（AI列を出力しない）を使用しても、AI分析自体は実行されます
- 処理速度を優先する場合は`--no-analyze-receipts`を使用してAI分析を完全に無効化してください
- モード3や4で必要な列のみを出力することで、出力ファイルのサイズを削減できます