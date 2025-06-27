import pytest
from unittest.mock import Mock, patch
from src.ocr_processor import OCRProcessor


class TestOCRProcessor:
    """OCRProcessorのテストクラス"""
    
    def test_単一画像ファイルのOCR処理が成功すること(self):
        # Arrange
        endpoint = "https://test.cognitiveservices.azure.com/"
        api_key = "test-api-key"
        processor = OCRProcessor(endpoint, api_key)
        
        # モックの設定
        mock_result = {
            "text": "これはOCRで読み取られたテキストです",
            "pages": [
                {
                    "page_number": 1,
                    "text": "これはOCRで読み取られたテキストです"
                }
            ]
        }
        
        with patch.object(processor, '_call_azure_api', return_value=mock_result):
            # Act
            result = processor.process_single_image("test.jpg", "様式A")
            
            # Assert
            assert result is not None
            assert "text" in result
            assert result["text"] == "これはOCRで読み取られたテキストです"
            assert len(result["pages"]) == 1
            assert result["pages"][0]["page_number"] == 1