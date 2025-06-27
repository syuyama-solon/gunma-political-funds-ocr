from typing import Dict, Any, Optional


class OCRProcessor:
    """Azure Document Intelligenceを使用したOCR処理クラス"""
    
    def __init__(self, endpoint: str, api_key: str):
        """
        OCRProcessorの初期化
        
        Args:
            endpoint: Azure Document Intelligenceのエンドポイント
            api_key: APIキー
        """
        self.endpoint = endpoint
        self.api_key = api_key
        
    def process_single_image(self, image_path: str, form_type: str) -> Optional[Dict[str, Any]]:
        """
        単一の画像ファイルをOCR処理する
        
        Args:
            image_path: 画像ファイルのパス
            form_type: 様式タイプ（例: "様式A", "様式B"）
            
        Returns:
            OCR結果を含む辞書。エラー時はNone
        """
        # テストを通すための最小限の実装
        result = self._call_azure_api(image_path, form_type)
        return result
    
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