import pytest
import logging
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
        
        # ファイルが存在することをモック
        with patch('os.path.exists', return_value=True):
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
    
    def test_OCR処理失敗時にエラーログが出力されスキップされること(self, caplog):
        # Arrange
        endpoint = "https://test.cognitiveservices.azure.com/"
        api_key = "test-api-key"
        processor = OCRProcessor(endpoint, api_key)
        
        # ファイルが存在することをモック
        with patch('os.path.exists', return_value=True):
            # APIエラーをシミュレート
            with patch.object(processor, '_call_azure_api', side_effect=Exception("API Error")):
                with caplog.at_level(logging.ERROR):
                    # Act
                    result = processor.process_single_image("broken.jpg", "様式A")
                    
                    # Assert
                    assert result is None
                    assert "Error processing broken.jpg" in caplog.text
                    assert "API Error" in caplog.text
    
    def test_ファイル読み込みエラー時にエラーログが出力されること(self, caplog):
        # Arrange
        endpoint = "https://test.cognitiveservices.azure.com/"
        api_key = "test-api-key"
        processor = OCRProcessor(endpoint, api_key)
        
        with caplog.at_level(logging.ERROR):
            # Act
            result = processor.process_single_image("nonexistent.jpg", "様式A")
            
            # Assert
            assert result is None
            assert "File not found" in caplog.text or "ファイルが見つかりません" in caplog.text