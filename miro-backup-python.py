import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging
import os
from dotenv import load_dotenv
from pathlib import Path

class MiroBoardBackup:
    """
    Miroボードのバックアップを行うクラス
    
    主な機能：
    - ボード情報の取得
    - ボード上の全アイテムの取得
    - JSONフォーマットでのバックアップ保存
    """
    
    def __init__(self, access_token: str):
        """
        MiroBoardBackupクラスの初期化
        
        引数:
            access_token (str): Miro APIのアクセストークン
                              開発者ポータルから取得可能
        """
        self.access_token = access_token
        self.base_url = "https://api.miro.com/v2"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        # ロギングの設定
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def get_board(self, board_id: str) -> Dict:
        """
        指定されたボードの情報を取得
        
        引数:
            board_id (str): バックアップ対象のMiroボードID
            
        戻り値:
            Dict: ボード情報（名前、作成者、権限など）
        """
        try:
            response = requests.get(
                f"{self.base_url}/boards/{board_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"ボード情報の取得に失敗しました: {str(e)}")
            raise

    def get_all_items(self, board_id: str) -> List[Dict]:
        """
        ボード上の全アイテムを取得
        
        引数:
            board_id (str): バックアップ対象のMiroボードID
            
        戻り値:
            List[Dict]: ボード上の全アイテムのリスト
        """
        items = []
        cursor = None
        
        try:
            while True:
                params = {"cursor": cursor} if cursor else {}
                response = requests.get(
                    f"{self.base_url}/boards/{board_id}/items",
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                items.extend(data.get("data", []))
                cursor = data.get("cursor")
                
                if not cursor:
                    break
                
                self.logger.debug(f"取得済みアイテム数: {len(items)}")
                    
            return items
        except requests.exceptions.RequestException as e:
            self.logger.error(f"アイテムの取得に失敗しました: {str(e)}")
            raise

    def backup_board(self, board_id: str, output_path: str) -> Dict:
        """
        Miroボードの完全バックアップを実行し、JSONファイルとして保存
        
        引数:
            board_id (str): バックアップ対象のMiroボードID
            output_path (str): バックアップJSONファイルの保存先パス
            
        戻り値:
            Dict: バックアップデータ全体
        """
        try:
            self.logger.info(f"ボード {board_id} のバックアップを開始します...")
            
            # ボード情報の取得
            board_info = self.get_board(board_id)
            self.logger.info(f"ボード情報の取得が完了しました: {board_info.get('name', 'Unknown Board')}")
            
            # 全アイテムの取得
            items = self.get_all_items(board_id)
            self.logger.info(f"全アイテムの取得が完了しました（合計: {len(items)}個）")
            
            # バックアップデータの作成
            backup_data = {
                "board": board_info,
                "items": items,
                "metadata": {
                    "backup_date": datetime.now().isoformat(),
                    "item_count": len(items),
                    "board_name": board_info.get('name', 'Unknown Board')
                }
            }
            
            # JSONファイルとして保存
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"バックアップが完了しました。保存先: {output_path}")
            self.logger.info(f"バックアップしたアイテム数: {len(items)}")
            
            return backup_data
            
        except Exception as e:
            self.logger.error(f"バックアップに失敗しました: {str(e)}")
            raise

def load_environment():
    """
    環境変数の読み込みを行う
    
    戻り値:
        tuple: (access_token, board_id, output_path)
    
    例外:
        環境変数が設定されていない場合に例外を発生
    """
    # .envファイルの読み込み
    env_path = Path('.') / '.env'
    load_dotenv(dotenv_path=env_path)
    
    # 必須の環境変数を取得
    access_token = os.getenv('MIRO_ACCESS_TOKEN')
    board_id = os.getenv('MIRO_BOARD_ID')
    
    # オプションの環境変数（デフォルト値あり）
    output_path = os.getenv('OUTPUT_PATH', 'miro_board_backup.json')
    
    # 必須の環境変数のチェック
    if not access_token:
        raise ValueError("環境変数 'MIRO_ACCESS_TOKEN' が設定されていません")
    if not board_id:
        raise ValueError("環境変数 'MIRO_BOARD_ID' が設定されていません")
        
    return access_token, board_id, output_path

def main():
    """
    メイン実行関数
    
    使用方法:
    1. .envファイルにMIRO_ACCESS_TOKEN、MIRO_BOARD_IDを設定
    2. スクリプトを実行
    """
    try:
        # 環境変数の読み込み
        access_token, board_id, output_path = load_environment()
        
        # バックアップの実行
        backup_service = MiroBoardBackup(access_token)
        backup_service.backup_board(board_id, output_path)
        
    except ValueError as e:
        logging.error(f"環境変数エラー: {str(e)}")
    except Exception as e:
        logging.error(f"バックアッププロセスが失敗しました: {str(e)}")

if __name__ == "__main__":
    main()