import os
import json
from typing import Dict, Optional
from dotenv import load_dotenv


class Config:
    """設定管理クラス"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        設定の初期化
        
        Args:
            config_file: 設定ファイルのパス（オプション）
        """
        # .envファイルを読み込む
        load_dotenv()
        
        # Azure設定
        self.endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT", "")
        self.api_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY", "")
        
        # OpenAI設定
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        
        # モデルマッピング
        self.model_mapping = self._load_model_mapping(config_file)
    
    def _load_model_mapping(self, config_file: Optional[str] = None) -> Dict[str, str]:
        """
        モデルマッピングを読み込む
        
        Args:
            config_file: 設定ファイルのパス
            
        Returns:
            様式名とモデルIDのマッピング
        """
        # 環境変数から読み込み（デフォルト）
        mapping = {
            "6-5": os.getenv("MODEL_ID_FORM_6_5", ""),
            "6-2-5": os.getenv("MODEL_ID_FORM_6_2_5", ""),
            "7-5": os.getenv("MODEL_ID_FORM_7_5", ""),
            "7-3-5": os.getenv("MODEL_ID_FORM_7_3_5", ""),
        }
        
        # 設定ファイルがあれば上書き
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                if "model_mapping" in config_data:
                    mapping.update(config_data["model_mapping"])
        
        # 空の値を除外
        return {k: v for k, v in mapping.items() if v}