import pytest
import os
import tempfile
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from src.ocr_processor import OCRProcessor


class TestBatchProcessor:
    """バッチ処理機能のテストクラス"""
    
    def test_フォルダ内の全画像がCSVに出力されること(self):
        # Arrange
        endpoint = "https://test.cognitiveservices.azure.com/"
        api_key = "test-api-key"
        processor = OCRProcessor(endpoint, api_key)
        
        # テスト用のファイルリスト
        test_files = ["image1.jpg", "image2.png", "image3.jpeg"]
        
        # 各ファイルのOCR結果をモック
        mock_results = [
            {
                "filename": "image1.jpg",
                "page": 1,
                "ocr_result": "ページ1のテキスト"
            },
            {
                "filename": "image2.png", 
                "page": 1,
                "ocr_result": "ページ2のテキスト"
            },
            {
                "filename": "image3.jpeg",
                "page": 1,
                "ocr_result": "ページ3のテキスト"
            }
        ]
        
        # os.listdirをモック
        with patch('os.listdir', return_value=test_files):
            with patch('os.path.exists', return_value=True):
                with patch.object(processor, 'process_single_image') as mock_process:
                    # 各画像の処理結果を設定
                    mock_process.side_effect = [
                        {"text": result["ocr_result"], "pages": [{"page_number": 1, "text": result["ocr_result"]}]}
                        for result in mock_results
                    ]
                    
                    # Act
                    df = processor.process_folder("./images", "6-5")
                    
                    # Assert
                    assert len(df) == 3
                    assert list(df.columns) == ["filename", "page", "ocr_result"]
                    assert df.iloc[0]["filename"] == "image1.jpg"
                    assert df.iloc[0]["page"] == 1
                    assert df.iloc[0]["ocr_result"] == "ページ1のテキスト"
    
    def test_CSV出力機能が正しく動作すること(self):
        # Arrange
        endpoint = "https://test.cognitiveservices.azure.com/"
        api_key = "test-api-key"
        processor = OCRProcessor(endpoint, api_key)
        
        # テストデータ
        test_data = pd.DataFrame([
            {"filename": "test1.jpg", "page": 1, "ocr_result": "テキスト1"},
            {"filename": "test2.jpg", "page": 1, "ocr_result": "テキスト2"}
        ])
        
        # 一時ファイルを使用
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
            output_path = tmp.name
            
        try:
            # Act
            processor.save_to_csv(test_data, output_path)
            
            # Assert
            assert os.path.exists(output_path)
            
            # CSVを読み込んで検証
            loaded_df = pd.read_csv(output_path)
            assert len(loaded_df) == 2
            assert list(loaded_df.columns) == ["filename", "page", "ocr_result"]
            assert loaded_df.iloc[0]["filename"] == "test1.jpg"
            
        finally:
            # クリーンアップ
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_非画像ファイルはスキップされること(self):
        # Arrange
        endpoint = "https://test.cognitiveservices.azure.com/"
        api_key = "test-api-key"
        processor = OCRProcessor(endpoint, api_key)
        
        # 画像ファイルと非画像ファイルを混在
        test_files = ["image1.jpg", "document.txt", "image2.png", "data.csv"]
        
        with patch('os.listdir', return_value=test_files):
            with patch('os.path.exists', return_value=True):
                with patch.object(processor, 'process_single_image') as mock_process:
                    mock_process.return_value = {"text": "テキスト", "pages": [{"page_number": 1, "text": "テキスト"}]}
                    
                    # Act
                    df = processor.process_folder("./images", "6-5")
                    
                    # Assert
                    # 画像ファイルのみ処理されている
                    assert len(df) == 2
                    assert mock_process.call_count == 2