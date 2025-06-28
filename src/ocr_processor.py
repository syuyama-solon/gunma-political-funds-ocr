import os
import logging
from typing import Dict, Any, Optional, List
import pandas as pd
from PIL import Image
import re
from .config import Config
from .receipt_analyzer import ReceiptAnalyzer

# ロガーの設定
logger = logging.getLogger(__name__)


class OCRProcessor:
    """Azure Document Intelligenceを使用したOCR処理クラス"""
    
    def __init__(self, endpoint: str, api_key: str, config: Optional[Config] = None, openai_api_key: Optional[str] = None):
        """
        OCRProcessorの初期化
        
        Args:
            endpoint: Azure Document Intelligenceのエンドポイント
            api_key: APIキー
            config: 設定オブジェクト（オプション）
            openai_api_key: OpenAI APIキー（オプション）
        """
        self.endpoint = endpoint
        self.api_key = api_key
        
        # 設定からモデルマッピングを読み込む
        if config:
            self.model_mapping = config.model_mapping
        else:
            self.model_mapping = {}  # 様式とモデルIDのマッピング
            
        # OpenAI解析器の初期化
        self.receipt_analyzer = None
        if openai_api_key:
            self.receipt_analyzer = ReceiptAnalyzer(openai_api_key)
        
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
                        
                        # receipt_imageフィールドの座標情報を保存
                        if field_name == "receipt_image" and hasattr(field_value, 'bounding_regions'):
                            if field_value.bounding_regions:
                                br = field_value.bounding_regions[0]
                                if hasattr(br, 'polygon') and br.polygon:
                                    # 座標を "x1,y1,x2,y2,x3,y3,x4,y4" 形式で保存
                                    doc_data["fields"]["receipt_image_area"] = ",".join(map(str, br.polygon))
                
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
    
    def process_folder(self, folder_path: str, form_type: str, extract_receipts: bool = True, analyze_receipts: bool = True) -> pd.DataFrame:
        """
        フォルダ内の全画像ファイルをOCR処理する
        
        Args:
            folder_path: 画像フォルダのパス
            form_type: 様式タイプ
            extract_receipts: 領収書画像を抽出するかどうか
            analyze_receipts: 領収書画像をOpenAIで解析するかどうか
            
        Returns:
            処理結果を含むDataFrame
        """
        results = []
        
        # サポートする画像形式
        supported_extensions = ('.png', '.jpg', '.jpeg', '.pdf')
        
        # 領収書画像の出力フォルダを作成
        if extract_receipts:
            receipt_folder = os.path.join(folder_path, "receipt_images")
            os.makedirs(receipt_folder, exist_ok=True)
        
        # フォルダ内のファイルを処理
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(supported_extensions):
                file_path = os.path.join(folder_path, filename)
                
                try:
                    result = self.process_single_image(file_path, form_type)
                    
                    if result and "documents" in result:
                        # 構造化されたフィールドの結果を処理
                        for doc_idx, doc in enumerate(result["documents"]):
                            if "fields" in doc:
                                row_data = {
                                    "folder_name": os.path.basename(folder_path),
                                    "filename": filename,
                                    "model_name": self.get_model_id(form_type),  # モデル名を追加
                                    "type": form_type  # 様式タイプを追加
                                }
                                
                                # receipt_image_area を最初に追加（typeの直後に配置するため）
                                if "receipt_image_area" in doc["fields"]:
                                    row_data["receipt_image_area"] = doc["fields"]["receipt_image_area"]
                                
                                # page_number_on_pdf を追加（ファイル名から抽出）
                                page_match = re.search(r'page_(\d+)', filename)
                                if page_match:
                                    row_data["page_number_on_pdf"] = int(page_match.group(1))
                                else:
                                    row_data["page_number_on_pdf"] = None
                                
                                # すべてのフィールドを列として追加（receipt_image_areaは既に追加済みなのでスキップ）
                                for field_name, field_value in doc["fields"].items():
                                    if field_name != "receipt_image_area":
                                        row_data[field_name] = field_value
                                
                                # 領収書画像を抽出
                                receipt_image_path = None
                                if extract_receipts and "receipt_image_area" in row_data:
                                    receipt_area = row_data["receipt_image_area"]
                                    if receipt_area:
                                        coords = self._parse_coordinates(receipt_area)
                                        if coords:
                                            base_name = os.path.splitext(filename)[0]
                                            receipt_filename = f"{base_name}_receipt_{doc_idx}.jpg"
                                            receipt_image_path = os.path.join(receipt_folder, receipt_filename)
                                            
                                            self._crop_and_save_image(
                                                file_path,
                                                coords,
                                                receipt_folder,
                                                filename,
                                                doc_idx
                                            )
                                            logger.info(f"Receipt image extracted from {filename}")
                                            
                                            # OpenAIで領収書を解析
                                            if analyze_receipts and self.receipt_analyzer and receipt_image_path:
                                                try:
                                                    receipt_info = self.receipt_analyzer.analyze_receipt_image(receipt_image_path)
                                                    # 解析結果を行データに追加
                                                    row_data["payee_name"] = receipt_info.get("payee_name", "")
                                                    row_data["payee_address"] = receipt_info.get("payee_address", "")
                                                    row_data["payment_date_extracted"] = receipt_info.get("payment_date", "")
                                                    row_data["payment_purpose"] = receipt_info.get("payment_purpose", "")
                                                    logger.info(f"Receipt analysis completed for {receipt_filename}")
                                                except Exception as e:
                                                    logger.error(f"Error analyzing receipt: {str(e)}")
                                                    row_data["payee_name"] = ""
                                                    row_data["payee_address"] = ""
                                                    row_data["payment_date_extracted"] = ""
                                                    row_data["payment_purpose"] = ""
                                
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
            # 列の順序を整理（folder_name, filename, model_name, type, receipt_image_area, page_number_on_pdf, page_numberを最初に配置）
            priority_cols = ["folder_name", "filename", "model_name", "type", "receipt_image_area", "page_number_on_pdf", "page_number",
                            "payee_name", "payee_address", "payment_date_extracted", "payment_purpose"]
            other_cols = [col for col in df.columns if col not in priority_cols]
            ordered_cols = [col for col in priority_cols if col in df.columns] + other_cols
            return df[ordered_cols]
        else:
            # 空のDataFrameを返す（構造化フィールド用の列）
            return pd.DataFrame(columns=["folder_name", "filename", "page_number"])
    
    def extract_receipt_images(self, folder_path: str, form_type: str, output_folder: str = "receipt_images") -> None:
        """
        座標情報を使って領収書画像を切り出して保存する
        
        Args:
            folder_path: 画像フォルダのパス
            form_type: 様式タイプ
            output_folder: 切り出した画像の保存先フォルダ
        """
        # 出力フォルダの作成
        os.makedirs(output_folder, exist_ok=True)
        
        # サポートする画像形式
        supported_extensions = ('.png', '.jpg', '.jpeg')
        
        # フォルダ内のファイルを処理
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(supported_extensions):
                file_path = os.path.join(folder_path, filename)
                
                try:
                    result = self.process_single_image(file_path, form_type)
                    
                    if result and "documents" in result:
                        # 構造化されたフィールドの結果を処理
                        for doc_idx, doc in enumerate(result["documents"]):
                            if "fields" in doc:
                                # receipt_image_areaの座標情報を取得
                                receipt_area = doc["fields"].get("receipt_image_area")
                                if receipt_area:
                                    # 座標を解析
                                    coords = self._parse_coordinates(receipt_area)
                                    if coords:
                                        # 画像を切り出して保存
                                        self._crop_and_save_image(
                                            file_path, 
                                            coords, 
                                            output_folder, 
                                            filename, 
                                            doc_idx
                                        )
                                        logger.info(f"Receipt image extracted from {filename}")
                    
                except Exception as e:
                    logger.error(f"Error extracting receipt from {filename}: {str(e)}")
                    continue
    
    def _parse_coordinates(self, coord_string: str) -> Optional[List[int]]:
        """
        座標文字列を解析してリストに変換
        
        Args:
            coord_string: 座標文字列（例: "1359,1341,1387,1971,112,2027,85,1397"）
            
        Returns:
            座標のリスト [x1, y1, x2, y2, x3, y3, x4, y4]
        """
        try:
            # Point形式の場合（例: "Point(x=1359.0, y=1341.0),Point(x=1387.0, y=1971.0),..."）
            if "Point(" in coord_string:
                pattern = r'[xy]=(\d+(?:\.\d+)?)'
                matches = re.findall(pattern, coord_string)
                if matches:
                    coords = [int(float(x)) for x in matches]
                    if len(coords) == 8:
                        return coords
            else:
                # カンマ区切りの数値を抽出
                coords = [int(x) for x in coord_string.split(",")]
                if len(coords) == 8:
                    return coords
                    
        except Exception as e:
            logger.error(f"Error parsing coordinates: {str(e)}")
            logger.error(f"Coordinate string: {coord_string}")
        
        return None
    
    def _crop_and_save_image(self, image_path: str, coords: List[int], 
                             output_folder: str, original_filename: str, 
                             doc_index: int) -> None:
        """
        画像を座標に基づいて切り出して保存
        
        Args:
            image_path: 元画像のパス
            coords: 座標リスト [x1, y1, x2, y2, x3, y3, x4, y4]
            output_folder: 保存先フォルダ
            original_filename: 元のファイル名
            doc_index: ドキュメントインデックス
        """
        try:
            # 画像を開く
            img = Image.open(image_path)
            
            # 座標から境界ボックスを計算（四角形の最小・最大座標）
            x_coords = coords[0::2]  # [x1, x2, x3, x4]
            y_coords = coords[1::2]  # [y1, y2, y3, y4]
            
            left = min(x_coords)
            top = min(y_coords)
            right = max(x_coords)
            bottom = max(y_coords)
            
            # 画像を切り出す
            cropped = img.crop((left, top, right, bottom))
            
            # ファイル名を生成
            base_name = os.path.splitext(original_filename)[0]
            output_filename = f"{base_name}_receipt_{doc_index}.jpg"
            output_path = os.path.join(output_folder, output_filename)
            
            # 保存
            cropped.save(output_path, "JPEG", quality=95)
            logger.info(f"Saved receipt image: {output_path}")
            
        except Exception as e:
            logger.error(f"Error cropping and saving image: {str(e)}")
    
    def save_to_csv(self, df: pd.DataFrame, output_path: str) -> None:
        """
        DataFrameをTSV（タブ区切り）ファイルに保存する
        
        Args:
            df: 保存するDataFrame
            output_path: 出力ファイルのパス（.tsv推奨）
        """
        # TSV形式で保存（タブ区切り）
        df.to_csv(output_path, index=False, encoding='utf-8-sig', sep='\t')
        logger.info(f"TSV saved to: {output_path}")