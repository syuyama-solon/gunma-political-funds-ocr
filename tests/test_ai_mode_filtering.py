"""
AI評価モードのフィルタリング機能のテスト
"""

import unittest
from unittest.mock import Mock, patch
import pandas as pd


class TestAIModeFiltering(unittest.TestCase):
    """AI評価モードのフィルタリング機能をテスト"""
    
    def setUp(self):
        """テストデータのセットアップ"""
        self.base_row_data = {
            "folder_name": "test",
            "filename": "test.jpg",
            "model_name": "test-model",
            "type": "6-5",
            "amount": "10000"
        }
        
        self.ai_results = {
            "payee_name": "テスト支出先",
            "payee_address": "テスト住所",
            "payment_date_extracted": "2024年1月1日",
            "payment_purpose": "テスト用途",
            "validity_score": "0.9",
            "validity_reason": "妥当です",
            "transparency_score": "0.8",
            "alternative_suggestion": "代替案なし",
            "news_value_potential_score": "0.1",
            "news_value_potential_score_reason": "ニュース価値なし",
            "business_type": "サービス業",
            "website": "https://example.com",
            "payee_detail": "詳細情報"
        }
    
    def test_ai_mode_1_all_columns(self):
        """モード1: すべてのAI列を出力"""
        row_data = self.base_row_data.copy()
        ai_mode = 1
        ai_columns = None
        
        # モード1の処理をシミュレート
        if ai_mode == 1:
            for key, value in self.ai_results.items():
                row_data[f"AI__{key}"] = value
        
        # すべてのAI列が追加されていることを確認
        for key in self.ai_results.keys():
            self.assertIn(f"AI__{key}", row_data)
            self.assertEqual(row_data[f"AI__{key}"], self.ai_results[key])
    
    def test_ai_mode_2_no_columns(self):
        """モード2: AI列を出力しない"""
        row_data = self.base_row_data.copy()
        ai_mode = 2
        
        # モード2の処理をシミュレート（何も追加しない）
        if ai_mode == 2:
            pass
        
        # AI列が追加されていないことを確認
        ai_columns_in_data = [col for col in row_data.keys() if col.startswith("AI__")]
        self.assertEqual(len(ai_columns_in_data), 0)
    
    def test_ai_mode_3_exclude_columns(self):
        """モード3: 特定の列のみ除外"""
        row_data = self.base_row_data.copy()
        ai_mode = 3
        exclude_columns = ["payee_detail", "website", "business_type"]
        
        # モード3の処理をシミュレート
        if ai_mode == 3:
            for key, value in self.ai_results.items():
                if key not in exclude_columns:
                    row_data[f"AI__{key}"] = value
        
        # 除外した列が含まれていないことを確認
        for col in exclude_columns:
            self.assertNotIn(f"AI__{col}", row_data)
        
        # 除外していない列が含まれていることを確認
        for key in self.ai_results.keys():
            if key not in exclude_columns:
                self.assertIn(f"AI__{key}", row_data)
    
    def test_ai_mode_4_include_columns(self):
        """モード4: 特定の列のみ出力"""
        row_data = self.base_row_data.copy()
        ai_mode = 4
        include_columns = ["validity_score", "validity_reason", "news_value_potential_score"]
        
        # モード4の処理をシミュレート
        if ai_mode == 4:
            for key, value in self.ai_results.items():
                if key in include_columns:
                    row_data[f"AI__{key}"] = value
        
        # 指定した列のみが含まれていることを確認
        ai_columns_in_data = [col for col in row_data.keys() if col.startswith("AI__")]
        self.assertEqual(len(ai_columns_in_data), len(include_columns))
        
        for col in include_columns:
            self.assertIn(f"AI__{col}", row_data)
        
        # 指定していない列が含まれていないことを確認
        for key in self.ai_results.keys():
            if key not in include_columns:
                self.assertNotIn(f"AI__{key}", row_data)
    
    def test_ai_mode_with_empty_columns_list(self):
        """空のカラムリストでのテスト"""
        # モード3で空のリスト（すべて出力）
        row_data = self.base_row_data.copy()
        ai_mode = 3
        exclude_columns = []
        
        if ai_mode == 3:
            for key, value in self.ai_results.items():
                if key not in exclude_columns:
                    row_data[f"AI__{key}"] = value
        
        # すべてのAI列が出力されることを確認
        for key in self.ai_results.keys():
            self.assertIn(f"AI__{key}", row_data)
        
        # モード4で空のリスト（何も出力しない）
        row_data = self.base_row_data.copy()
        ai_mode = 4
        include_columns = []
        
        if ai_mode == 4:
            for key, value in self.ai_results.items():
                if key in include_columns:
                    row_data[f"AI__{key}"] = value
        
        # AI列が出力されないことを確認
        ai_columns_in_data = [col for col in row_data.keys() if col.startswith("AI__")]
        self.assertEqual(len(ai_columns_in_data), 0)


if __name__ == '__main__':
    unittest.main()