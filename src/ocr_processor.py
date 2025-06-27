import os
import logging
from typing import Dict, Any, Optional
from .config import Config

# ロガーの設定
logger = logging.getLogger(__name__)


class OCRProcessor:
    """Azure Document Intelligenceを使用したOCR処理クラス"""
    
    def __init__(self, endpoint: str, api_key: str, config: Optional[Config] = None):
        """
        OCRProcessorの初期化
        
        Args:
            endpoint: Azure Document Intelligenceのエンドポイント
            api_key: APIキー
            config: 設定オブジェクト（オプション）
        """
        self.endpoint = endpoint
        self.api_key = api_key
        
        # 設定からモデルマッピングを読み込む
        if config:
            self.model_mapping = config.model_mapping
        else:
            self.model_mapping = {}  # 様式とモデルIDのマッピング
        
    def process_single_image(self, image_path: str, form_type: str) -> Optional[Dict[str, Any]]:
        """
        単一の画像ファイルをOCR処理する
        
        Args:
            image_path: 画像ファイルのパス
            form_type: 様式タイプ（例: "様式A", "様式B"）
            
        Returns:
            OCR結果を含む辞書。エラー時はNone
        """
        try:
            # ファイルの存在確認
            if not os.path.exists(image_path):
                logger.error(f"File not found: {image_path}")
                return None
            
            # APIを呼び出す
            result = self._call_azure_api(image_path, form_type)
            return result
            
        except Exception as e:
            logger.error(f"Error processing {image_path}: {str(e)}")
            return None
    
    def get_model_id(self, form_type: str) -> Optional[str]:
        """
        様式タイプに対応するモデルIDを取得する
        
        Args:
            form_type: 様式タイプ
            
        Returns:
            モデルID。未定義の場合はNone
        """
        return self.model_mapping.get(form_type)
    
    def _call_azure_api(self, image_path: str, form_type: str) -> Dict[str, Any]:
        """
        Azure APIを呼び出す（プライベートメソッド）
        
        Args:
            image_path: 画像ファイルのパス
            form_type: 様式タイプ
            
        Returns:
            API応答
        """
        # 実際のAPI呼び出しは後で実装
        pass