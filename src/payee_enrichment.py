import logging
from typing import Dict, Optional, List
from openai import OpenAI
import json
import time
from datetime import datetime, timedelta

# ロガーの設定
logger = logging.getLogger(__name__)


class PayeeEnrichmentService:
    """支出先情報を外部データで補完するサービス"""
    
    def __init__(self, api_key: str):
        """
        PayeeEnrichmentServiceの初期化
        
        Args:
            api_key: OpenAI APIキー
        """
        self.client = OpenAI(api_key=api_key)
        self.cache = {}  # 簡易キャッシュ
        self.cache_expiry = {}  # キャッシュ有効期限
        
    def enrich_payee_info(self, payee_name: str, payee_address: str = "", 
                         use_cache: bool = True) -> Dict[str, str]:
        """
        支出先情報を補完
        
        Args:
            payee_name: 支出先名
            payee_address: 支出先住所
            use_cache: キャッシュを使用するか
            
        Returns:
            補完された情報の辞書
        """
        # キャッシュチェック
        cache_key = f"{payee_name}_{payee_address}"
        if use_cache and cache_key in self.cache:
            if datetime.now() < self.cache_expiry.get(cache_key, datetime.min):
                logger.info(f"Using cached data for {payee_name}")
                return self.cache[cache_key]
        
        try:
            # GPT-4o-miniで企業情報を生成
            prompt = f"""
            以下の企業・団体について、公知の情報を基に詳細情報を提供してください。
            推測や不確実な情報は含めないでください。
            
            企業・団体名: {payee_name}
            住所: {payee_address if payee_address else "不明"}
            
            以下の形式でJSONで回答してください：
            {{
                "business_type": "業種（例：飲食業、小売業、サービス業等）",
                "business_description": "事業内容の簡潔な説明",
                "establishment_year": "設立年（分かる場合のみ、不明なら空文字）",
                "capital": "資本金（分かる場合のみ、不明なら空文字）",
                "employees": "従業員数（分かる場合のみ、不明なら空文字）",
                "website": "ウェブサイト（分かる場合のみ、不明なら空文字）",
                "notes": "その他の注記事項"
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "あなたは企業情報の専門家です。確実な情報のみを提供してください。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # より事実に基づいた回答を得るため低めに設定
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # 結果を整形
            enriched_info = {
                "business_type": result.get("business_type", "不明"),
                "business_description": result.get("business_description", ""),
                "establishment_year": result.get("establishment_year", ""),
                "capital": result.get("capital", ""),
                "employees": result.get("employees", ""),
                "website": result.get("website", ""),
                "notes": result.get("notes", ""),
                "enrichment_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # キャッシュに保存（24時間有効）
            self.cache[cache_key] = enriched_info
            self.cache_expiry[cache_key] = datetime.now() + timedelta(hours=24)
            
            logger.info(f"Enriched information for {payee_name}")
            return enriched_info
            
        except Exception as e:
            logger.error(f"Error enriching payee info for {payee_name}: {str(e)}")
            return {
                "business_type": "エラー",
                "business_description": "情報取得エラー",
                "establishment_year": "",
                "capital": "",
                "employees": "",
                "website": "",
                "notes": str(e),
                "enrichment_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def batch_enrich_payees(self, payees: List[Dict[str, str]], 
                           batch_size: int = 10) -> List[Dict[str, str]]:
        """
        複数の支出先情報を一括で補完
        
        Args:
            payees: 支出先情報のリスト
            batch_size: バッチサイズ
            
        Returns:
            補完された情報のリスト
        """
        enriched_results = []
        
        for i in range(0, len(payees), batch_size):
            batch = payees[i:i + batch_size]
            
            for payee in batch:
                enriched_info = self.enrich_payee_info(
                    payee.get("name", ""),
                    payee.get("address", "")
                )
                
                # 元の情報と補完情報を結合
                result = payee.copy()
                result.update(enriched_info)
                enriched_results.append(result)
                
                # レート制限対策
                time.sleep(0.5)
        
        return enriched_results
    
    def export_cache_stats(self) -> Dict[str, int]:
        """
        キャッシュの統計情報を出力
        
        Returns:
            キャッシュ統計
        """
        active_cache = sum(
            1 for key, expiry in self.cache_expiry.items() 
            if datetime.now() < expiry
        )
        
        return {
            "total_cached": len(self.cache),
            "active_cache": active_cache,
            "expired_cache": len(self.cache) - active_cache
        }