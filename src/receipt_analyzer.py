import base64
import logging
from typing import Dict, Optional, Any
from openai import OpenAI
from PIL import Image
import io

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
        
    def analyze_receipt_image(self, image_path: str) -> Dict[str, Optional[str]]:
        """
        領収書画像を解析して情報を抽出
        
        Args:
            image_path: 画像ファイルのパス
            
        Returns:
            抽出された情報の辞書 {
                "payee_name": "支出先名",
                "payee_address": "支出先住所",
                "payment_date": "支出日",
                "payment_purpose": "支払い用途"
            }
        """
        try:
            # 画像をbase64エンコード
            base64_image = self._encode_image(image_path)
            
            # プロンプトの設定
            prompt = """
            この領収書画像から以下の情報を抽出してください。日本語で回答してください。
            情報が見つからない場合は「不明」と回答してください。
            
            1. 支出先名（店舗名・会社名）
            2. 支出先住所
            3. 支出日（YYYY年MM月DD日形式）
            4. 支払い用途（何のための支払いか）
            
            JSONフォーマットで回答してください：
            {
                "payee_name": "支出先名",
                "payee_address": "支出先住所",
                "payment_date": "支出日",
                "payment_purpose": "支払い用途"
            }
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
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            # レスポンスから情報を抽出
            import json
            result = json.loads(response.choices[0].message.content)
            
            logger.info(f"Receipt analysis completed for {image_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing receipt {image_path}: {str(e)}")
            return {
                "payee_name": "エラー",
                "payee_address": "エラー",
                "payment_date": "エラー",
                "payment_purpose": "エラー"
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