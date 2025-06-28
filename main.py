#!/usr/bin/env python3
"""
Azure Document IntelligenceによるOCR処理システム
群馬県政治資金PDFファイル電子化プロジェクト
"""

import argparse
import logging
import sys
from pathlib import Path
from src.ocr_processor import OCRProcessor
from src.config import Config


def setup_logging(verbose: bool = False):
    """ロギングの設定"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='Azure Document Intelligenceを使用した画像OCR処理'
    )
    parser.add_argument(
        'input_folder',
        type=str,
        help='処理する画像が含まれるフォルダのパス'
    )
    parser.add_argument(
        'form_type',
        type=str,
        help='処理する様式タイプ（6-5, 6-2-5, 7-5, 7-3-5）'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='output.tsv',
        help='出力TSVファイルのパス（デフォルト: output.tsv）'
    )
    parser.add_argument(
        '-c', '--config',
        type=str,
        help='設定ファイルのパス（JSON形式）'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='詳細なログ出力を有効にする'
    )
    
    parser.add_argument(
        '--no-extract-receipts',
        action='store_true',
        help='領収書画像の抽出を無効にする'
    )
    
    parser.add_argument(
        '--no-analyze-receipts',
        action='store_true',
        help='領収書画像のOpenAI解析を無効にする'
    )
    
    args = parser.parse_args()
    
    # ロギング設定
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # 設定の読み込み
        logger.info("設定を読み込んでいます...")
        config = Config(args.config)
        
        if not config.endpoint or not config.api_key:
            logger.error("Azure Document Intelligenceのエンドポイントとキーが設定されていません。")
            logger.error(".envファイルまたは環境変数を確認してください。")
            sys.exit(1)
        
        # OCRプロセッサの初期化
        logger.info("OCRプロセッサを初期化しています...")
        processor = OCRProcessor(
            endpoint=config.endpoint,
            api_key=config.api_key,
            config=config,
            openai_api_key=config.openai_api_key
        )
        
        # 入力フォルダの確認
        input_path = Path(args.input_folder)
        if not input_path.exists():
            logger.error(f"入力フォルダが見つかりません: {input_path}")
            sys.exit(1)
        
        # 様式の確認
        if args.form_type not in processor.model_mapping:
            logger.error(f"未定義の様式です: {args.form_type}")
            logger.error(f"利用可能な様式: {', '.join(processor.model_mapping.keys())}")
            sys.exit(1)
        
        # バッチ処理の実行
        logger.info(f"フォルダ内の画像を処理しています: {input_path}")
        logger.info(f"様式: {args.form_type}")
        
        # 領収書画像抽出の設定
        extract_receipts = not args.no_extract_receipts
        analyze_receipts = not args.no_analyze_receipts
        
        if extract_receipts:
            logger.info("領収書画像の抽出を有効にしています")
        if analyze_receipts and config.openai_api_key:
            logger.info("領収書画像のOpenAI解析を有効にしています")
        elif analyze_receipts and not config.openai_api_key:
            logger.warning("OpenAI APIキーが設定されていません。領収書解析はスキップされます。")
            analyze_receipts = False
        
        df = processor.process_folder(
            str(input_path), 
            args.form_type, 
            extract_receipts=extract_receipts,
            analyze_receipts=analyze_receipts
        )
        
        if df.empty:
            logger.warning("処理対象のファイルが見つかりませんでした。")
            sys.exit(0)
        
        # 結果の保存
        logger.info(f"処理結果をTSVに保存しています: {args.output}")
        processor.save_to_csv(df, args.output)
        
        logger.info(f"処理完了: {len(df)}件のページを処理しました。")
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()