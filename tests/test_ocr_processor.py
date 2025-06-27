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
    
    def test_指定された様式に応じて適切なモデルが選択されること(self):
        # Arrange
        endpoint = "https://test.cognitiveservices.azure.com/"
        api_key = "test-api-key"
        processor = OCRProcessor(endpoint, api_key)
        
        # モデルマッピングを設定
        processor.model_mapping = {
            "様式A": "model_id_a",
            "様式B": "model_id_b",
            "様式C": "model_id_c"
        }
        
        # Act & Assert
        assert processor.get_model_id("様式A") == "model_id_a"
        assert processor.get_model_id("様式B") == "model_id_b"
        assert processor.get_model_id("様式C") == "model_id_c"
    
    def test_未定義の様式が指定された場合はNoneを返すこと(self):
        # Arrange
        endpoint = "https://test.cognitiveservices.azure.com/"
        api_key = "test-api-key"
        processor = OCRProcessor(endpoint, api_key)
        
        processor.model_mapping = {
            "様式A": "model_id_a",
            "様式B": "model_id_b"
        }
        
        # Act & Assert
        assert processor.get_model_id("様式Z") is None