import base64
import logging
import re
from typing import Dict, Optional, Any
from openai import OpenAI
from PIL import Image
import io
from .payee_enrichment import PayeeEnrichmentService

# ロガーの設定
logger = logging.getLogger(__name__)


class ReceiptAnalyzer:
    """OpenAI Vision APIを使用した領収書画像解析クラス"""
    
    def __init__(self, api_key: str):
        """
        ReceiptAnalyzerの初期化
        
        Args:
            api_key: OpenAI APIキー
        """
        self.client = OpenAI(api_key=api_key)
        self.enrichment_service = PayeeEnrichmentService(api_key)
        
    def _parse_amount(self, amount_str: str) -> Optional[int]:
        """
        金額文字列を数値に変換
        
        Args:
            amount_str: 金額文字列（例: "14,840円", "¥5,020"）
            
        Returns:
            金額の数値、解析できない場合はNone
        """
        try:
            # 数字以外の文字を除去
            cleaned = re.sub(r'[^\d,]', '', amount_str)
            # カンマを除去
            cleaned = cleaned.replace(',', '')
            # 数値に変換
            return int(cleaned) if cleaned else None
        except:
            return None
    
    def analyze_receipt_image(self, image_path: str, activity_description: str = "", amount: str = "") -> Dict[str, Optional[str]]:
        """
        領収書画像を解析して情報を抽出
        
        Args:
            image_path: 画像ファイルのパス
            activity_description: 活動内容の説明（妥当性評価用）
            amount: 支出金額（妥当性評価用）
            
        Returns:
            抽出された情報の辞書 {
                "payee_name": "支出先名",
                "payee_address": "支出先住所",
                "payment_date": "支出日",
                "payment_purpose": "支払い用途",
                "validity_score": "妥当性スコア",
                "validity_reason": "妥当性理由",
                "payee_detail": "支出先詳細",
                "transparency_score": "透明性スコア",
                "alternative_suggestion": "代替案",
                "news_value_potential_score": "ニュース価値スコア",
                "news_value_potential_reason": "ニュース価値の理由"
            }
        """
        try:
            # 画像をbase64エンコード
            base64_image = self._encode_image(image_path)
            
            # 金額を数値として解析
            amount_numeric = self._parse_amount(amount) if amount else None
            amount_info = f"支出金額: {amount}"
            if amount_numeric:
                amount_info += f" ({amount_numeric:,}円)"
            
            # プロンプトの設定
            prompt = f"""
            この領収書画像から以下の情報を抽出し、政務活動費としての妥当性を評価してください。日本語で回答してください。
            情報が見つからない場合は「不明」と回答してください。
            
            活動内容: {activity_description}
            {amount_info}
            
            1. 支出先名（店舗名・会社名）
            2. 支出先住所
            3. 支出日（YYYY年MM月DD日形式）
            4. 支払い用途（何のための支払いか）
            5. 政務活動費としての妥当性スコア（0.0〜1.0、明確な法令違反は-1）
               評価基準：
               - 支出目的の適切性（政務活動との関連性）
               - 金額の妥当性（社会通念上の適正額かどうか）
               - 支出先の適切性
               
               金額の目安：
               - 研修・セミナー参加費: 5,000円～50,000円程度が一般的
               - 交通費（新幹線）: 実費相当額
               - 会議費（1人あたり）: 5,000円以下
               - 書籍・資料: 実費相当額
               - 事務用品: 実費相当額（高額品は要注意）
               
               スコア基準：
               - 1.0: 完全に妥当（目的・金額・支出先すべて適切）
               - 0.8-0.9: 概ね妥当（軽微な疑問点あり）
               - 0.5-0.7: 疑問あり（金額が高額または目的が不明確）
               - 0.1-0.4: 不適切の可能性高い（著しく高額または目的外）
               - 0.0: 不適切（明らかに政務活動外）
               - -1: 明確な法令違反（違法行為への支出等）
            6. 妥当性評価の理由（金額の適正性も含めて具体的に）
            7. 支出先の詳細情報（業種、事業内容など把握できる範囲で）
            8. 透明性スコア（0.0～1.0）
               領収書の詳細度・明確さの評価基準：
               - 1.0: 完璧（支出先、日付、金額、具体的な品目・サービス内容がすべて明確）
               - 0.8-0.9: 優秀（基本情報は明確だが、一部詳細が不足）
               - 0.5-0.7: 普通（最低限の情報はあるが、詳細が不明確）
               - 0.2-0.4: 不十分（重要な情報が欠けている、または曖昧）
               - 0.0-0.1: 非常に不透明（「品代」「その他」など具体性なし）
            9. 代替案の提案（もっと効率的・経済的な方法があれば具体的に提案）
               例：
               - 「オンライン会議なら交通費不要」
               - 「電子書籍版なら30%安価」
               - 「一括購入で単価削減可能」
               - 該当なしの場合は「特になし」
            10. ニュース価値ポテンシャルスコア（0.0～1.0）
               新聞・テレビ・週刊誌記者にとって興味深いネタになる可能性の評価：
               - 1.0: 極めて高い（スキャンダル性、不正疑惑、極端な浪費）
               - 0.7-0.9: 高い（異常な高額支出、疑わしい支出先、不透明な用途）
               - 0.4-0.6: 中程度（やや高額、説明不足、グレーゾーン）
               - 0.1-0.3: 低い（一般的だが批判の余地あり）
               - 0.0: なし（完全に通常の支出）
               
               評価のポイント：
               - 金額の異常性（社会通念から大きく逸脱）
               - 支出先の特殊性（風俗関連、高級店、個人的趣味）
               - 用途の不明確さ（「品代」など曖昧な記載）
               - タイミングの疑惑（選挙前、深夜など）
               - 頻度の異常性（同一店舗への頻繁な支出）
            11. ニュース価値ポテンシャルの理由（記者が注目しそうなポイントを具体的に）
            
            JSONフォーマットで回答してください：
            {{
                "payee_name": "支出先名",
                "payee_address": "支出先住所",
                "payment_date": "支出日",
                "payment_purpose": "支払い用途",
                "validity_score": 0.0,
                "validity_reason": "妥当性評価の理由",
                "payee_detail": "支出先の詳細情報",
                "transparency_score": 0.0,
                "alternative_suggestion": "代替案の提案",
                "news_value_potential_score": 0.0,
                "news_value_potential_reason": "ニュース価値の理由"
            }}
            """
            
            # OpenAI APIを呼び出し
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # より高速で安価なモデル
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            # レスポンスから情報を抽出
            import json
            result = json.loads(response.choices[0].message.content)
            
            # 支出先情報のエンリッチメント
            payee_name = result.get("payee_name", "")
            payee_address = result.get("payee_address", "")
            
            if payee_name and payee_name != "不明" and payee_name != "エラー":
                enriched_info = self.enrichment_service.enrich_payee_info(
                    payee_name, payee_address
                )
                
                # 詳細情報を結合
                payee_detail_parts = []
                if enriched_info.get("business_type"):
                    payee_detail_parts.append(f"業種: {enriched_info['business_type']}")
                if enriched_info.get("business_description"):
                    payee_detail_parts.append(f"事業内容: {enriched_info['business_description']}")
                if enriched_info.get("establishment_year"):
                    payee_detail_parts.append(f"設立: {enriched_info['establishment_year']}")
                if enriched_info.get("website"):
                    payee_detail_parts.append(f"Web: {enriched_info['website']}")
                
                result["payee_detail"] = " / ".join(payee_detail_parts) if payee_detail_parts else result.get("payee_detail", "")
            
            logger.info(f"Receipt analysis completed for {image_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing receipt {image_path}: {str(e)}")
            return {
                "payee_name": "エラー",
                "payee_address": "エラー",
                "payment_date": "エラー",
                "payment_purpose": "エラー",
                "validity_score": "エラー",
                "validity_reason": "エラー",
                "payee_detail": "エラー",
                "transparency_score": "エラー",
                "alternative_suggestion": "エラー",
                "news_value_potential_score": "エラー",
                "news_value_potential_reason": "エラー"
            }
    
    def _encode_image(self, image_path: str) -> str:
        """
        画像をbase64エンコード
        
        Args:
            image_path: 画像ファイルのパス
            
        Returns:
            base64エンコードされた文字列
        """
        # 画像を開いて最適化
        with Image.open(image_path) as img:
            # 画像が大きすぎる場合はリサイズ
            max_size = (1024, 1024)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # JPEGとして保存
            buffer = io.BytesIO()
            # RGBモードに変換（透過画像対応）
            if img.mode in ('RGBA', 'LA'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img
            
            img.save(buffer, format="JPEG", quality=85)
            buffer.seek(0)
            
            # base64エンコード
            return base64.b64encode(buffer.read()).decode('utf-8')