import os
import logging
from typing import Dict, Any, Optional, List
import pandas as pd
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
        from azure.ai.formrecognizer import DocumentAnalysisClient
        from azure.core.credentials import AzureKeyCredential
        
        # モデルIDの取得
        model_id = self.get_model_id(form_type)
        if not model_id:
            raise ValueError(f"モデルIDが見つかりません: {form_type}")
        
        # クライアントの初期化
        client = DocumentAnalysisClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.api_key)
        )
        
        # ファイルを読み込む
        with open(image_path, "rb") as f:
            # カスタムモデルで分析を開始
            poller = client.begin_analyze_document(
                model_id=model_id,
                document=f
            )
            result = poller.result()
        
        # 結果を整形 - documentsセクションから構造化データを抽出
        if hasattr(result, 'documents') and result.documents:
            # カスタムモデルの結果を返す
            documents = []
            for doc in result.documents:
                doc_data = {
                    "doc_type": doc.doc_type if hasattr(doc, 'doc_type') else None,
                    "fields": {}
                }
                
                # フィールドを抽出
                if hasattr(doc, 'fields') and doc.fields:
                    for field_name, field_value in doc.fields.items():
                        if hasattr(field_value, 'value_string') and field_value.value_string:
                            doc_data["fields"][field_name] = field_value.value_string
                        elif hasattr(field_value, 'content') and field_value.content:
                            doc_data["fields"][field_name] = field_value.content
                        else:
                            doc_data["fields"][field_name] = None
                
                documents.append(doc_data)
            
            return {"documents": documents}
        else:
            # 通常のテキスト抽出（フォールバック）
            pages = []
            full_text = []
            
            for page_idx, page in enumerate(result.pages):
                page_text = ""
                
                # 各ページのコンテンツを抽出
                if hasattr(page, 'lines') and page.lines:
                    for line in page.lines:
                        page_text += line.content + "\n"
                
                pages.append({
                    "page_number": page_idx + 1,
                    "text": page_text.strip()
                })
                full_text.append(page_text)
            
            return {
                "text": "\n".join(full_text).strip(),
                "pages": pages
            }
    
    def process_folder(self, folder_path: str, form_type: str) -> pd.DataFrame:
        """
        フォルダ内の全画像ファイルをOCR処理する
        
        Args:
            folder_path: 画像フォルダのパス
            form_type: 様式タイプ
            
        Returns:
            処理結果を含むDataFrame
        """
        results = []
        
        # サポートする画像形式
        supported_extensions = ('.png', '.jpg', '.jpeg', '.pdf')
        
        # フォルダ内のファイルを処理
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(supported_extensions):
                file_path = os.path.join(folder_path, filename)
                
                try:
                    result = self.process_single_image(file_path, form_type)
                    
                    if result and "documents" in result:
                        # 構造化されたフィールドの結果を処理
                        for doc in result["documents"]:
                            if "fields" in doc:
                                row_data = {
                                    "folder_name": os.path.basename(folder_path),
                                    "filename": filename
                                }
                                
                                # すべてのフィールドを列として追加
                                for field_name, field_value in doc["fields"].items():
                                    row_data[field_name] = field_value
                                
                                results.append(row_data)
                    elif result and "pages" in result:
                        # フォールバック: 通常のテキスト抽出
                        for page in result["pages"]:
                            results.append({
                                "filename": filename,
                                "page": page["page_number"],
                                "ocr_result": page["text"]
                            })
                    
                except Exception as e:
                    logger.error(f"Error processing {filename}: {str(e)}")
                    continue
        
        # DataFrameに変換
        if results:
            df = pd.DataFrame(results)
            # 列の順序を整理（folder_name, filename, page_numberを最初に配置）
            priority_cols = ["folder_name", "filename", "page_number"]
            other_cols = [col for col in df.columns if col not in priority_cols]
            ordered_cols = [col for col in priority_cols if col in df.columns] + other_cols
            return df[ordered_cols]
        else:
            # 空のDataFrameを返す（構造化フィールド用の列）
            return pd.DataFrame(columns=["folder_name", "filename", "page_number"])
    
    def save_to_csv(self, df: pd.DataFrame, output_path: str) -> None:
        """
        DataFrameをCSVファイルに保存する
        
        Args:
            df: 保存するDataFrame
            output_path: 出力CSVファイルのパス
        """
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        logger.info(f"CSV saved to: {output_path}")