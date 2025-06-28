# AI評価モード実行結果

## テスト実行結果

### モード1: すべてのAI列を出力（デフォルト）
```bash
python3 main.py ./test_images 6-5 -o mode1_all_ai.tsv
```

**結果:**
- 総列数: 23列
- AI列数: 13列
- AI列: 
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

### モード2: AI列を出力しない
```bash
python3 main.py ./test_images 6-5 -o mode2_no_ai.tsv --ai-mode 2
```

**結果:**
- 総列数: 10列
- AI列数: 0列
- 基本情報のみ（OCR結果のみ）

### モード3: 特定の列のみ除外
```bash
python3 main.py ./test_images 6-5 -o mode3_exclude.tsv --ai-mode 3 --ai-columns payee_detail website business_type
```

**結果:**
- 総列数: 20列
- AI列数: 10列
- 除外された列: AI__payee_detail, AI__website, AI__business_type
- 残ったAI列: 妥当性評価、透明性評価、ニュース価値評価など主要な評価項目

### モード4: 特定の列のみ出力
```bash
python3 main.py ./test_images 6-5 -o mode4_include.tsv --ai-mode 4 --ai-columns validity_score validity_reason news_value_potential_score
```

**結果:**
- 総列数: 13列
- AI列数: 3列
- 出力されたAI列: 
  - AI__validity_score（妥当性スコア）
  - AI__validity_reason（妥当性評価の理由）
  - AI__news_value_potential_score（ニュース価値スコア）

## サンプルデータ

### 研修参加費の例（1行目）
- **支出内容**: 研修参加費 10,000円
- **支出先**: 地方議員研究会
- **妥当性スコア**: 0.9（高い妥当性）
- **妥当性理由**: "研修参加費用として適切であり、金額も社会通念内"
- **ニュース価値**: 0.1（低い）
- **理由**: "一般的な研修費用であり、特に目立つポイントはない"

### 会議費の例（2行目）
- **支出内容**: 会議費 20,000円
- **支出先**: 〇〇ホテル会議室
- **妥当性スコア**: 0.8（概ね妥当）
- **妥当性理由**: "会議費として妥当だが、参加者リストの添付が望ましい"
- **ニュース価値**: 0.3（中程度）
- **理由**: "高額な会議費のため、やや注目される可能性あり"

### 交通費の例（3行目）
- **支出内容**: 交通費 30,000円
- **支出先**: 東日本旅客鉄道株式会社
- **妥当性スコア**: 0.95（非常に高い妥当性）
- **妥当性理由**: "公務での移動として適切"
- **ニュース価値**: 0.05（非常に低い）
- **理由**: "通常の交通費で問題なし"

## 使用場面の推奨

1. **モード1（デフォルト）**: 詳細な分析が必要な場合、初回の確認時
2. **モード2**: OCR結果のみ必要な場合、AI分析が不要な場合
3. **モード3**: 詳細情報（payee_detail等）を除外してファイルサイズを削減したい場合
4. **モード4**: 重要な評価指標のみ抽出してレポート作成する場合