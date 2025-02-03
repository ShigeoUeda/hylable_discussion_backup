from typing import List, Dict, Union
from pathlib import Path
import hylable
import time
from datetime import datetime
import pytz
from tqdm import tqdm

# Hylableクライアントの初期化
hy_client = hylable.HDClient(profile_name="default")

def seconds_to_time_format(seconds: int) -> str:
    """
    秒数を「00_00_00」形式に変換します。

    Args:
        seconds (int): 変換する秒数

    Returns:
        str: 「00_00_00」形式の文字列
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60
    return f"{hours:02d}_{minutes:02d}_{remaining_seconds:02d}"

def get_recording_discussion_ids(
    hy_client: hylable.HDClient,
    course_id: str,
    max_discussions: int = 3,
    timeout: int = 30
) -> List[str]:
    """
    指定されたコースから録音中のディスカッションIDを取得します。

    Args:
        hy_client (hylable.HDClient): Hylableクライアントインスタンス
        course_id (str): 対象のコースID
        max_discussions (int, optional): 取得する最大ディスカッション数。デフォルトは3。
        timeout (int, optional): タイムアウトまでの秒数。デフォルトは30秒。

    Returns:
        List[str]: 録音中のディスカッションIDのリスト
    """
    discussion_ids: List[str] = []
    start_time = time.time()
    
    while len(discussion_ids) < max_discussions:
        for discussion in hy_client.get_discussions(course_id):
            if discussion.status == "recording":
                if discussion.id not in discussion_ids:
                    discussion_ids.append(discussion.id)
                    print(f"Found recording discussion: {discussion.id}")
                
                if len(discussion_ids) >= max_discussions:
                    print(f"Reached maximum number of discussions: {max_discussions}")
                    return discussion_ids
        
        if time.time() - start_time > timeout:
            print(f"Timeout reached after {timeout} seconds")
            break    
    return discussion_ids

def get_discussion_ids(
    hy_client: hylable.HDClient,
    course_id: str,
    max_discussions: int = 3,
    timeout: int = 30
) -> List[str]:
    """
    指定されたコースからディスカッションIDを取得します。
    録音中、非録音に関わらずすべてのディスカッションを対象とします。

    Args:
        hy_client (hylable.HDClient): Hylableクライアントインスタンス
        course_id (str): 対象のコースID
        max_discussions (int, optional): 取得する最大ディスカッション数。デフォルトは3。
        timeout (int, optional): タイムアウトまでの秒数。デフォルトは30秒。

    Returns:
        List[str]: ディスカッションIDのリスト

    Notes:
        - 指定されたmax_discussions数に達するか、timeout秒が経過するまでディスカッションを取得します。
        - 3秒間隔でディスカッションの取得を試みます。
    """
    discussion_ids: List[str] = []
    start_time = time.time()
    
    while len(discussion_ids) < max_discussions:
        for discussion in hy_client.get_discussions(course_id):
            if discussion.id not in discussion_ids:
                discussion_ids.append(discussion.id)
                print(f"Found discussion: {discussion.id}")
                
                if len(discussion_ids) >= max_discussions:
                    print(f"Reached maximum number of discussions: {max_discussions}")
                    return discussion_ids
        
        if time.time() - start_time > timeout:
            print(f"Timeout reached after {timeout} seconds")
            break
        
        time.sleep(3)
    
    return discussion_ids

#-----

def get_all_discussion_ids(
    hy_client: hylable.HDClient,
    course_id: str,
    timeout: int = 30
) -> List[Dict[str, str]]:
    """
    指定されたコースからすべてのディスカッションIDとその情報を取得します。
    録音中、非録音に関わらずすべてのディスカッションを対象とします。
    録音日時はJST（日本時間）で表示されます。

    Args:
        hy_client (hylable.HDClient): Hylableクライアントインスタンス
        course_id (str): 対象のコースID
        timeout (int, optional): タイムアウトまでの秒数。デフォルトは30秒。

    Returns:
        List[Dict[str, str]]: ディスカッションIDと詳細情報を含む辞書のリスト
            {
                'id': ディスカッションID,
                'status': 録音状態,
                'topic': トピック,
                'comment': コメント,
                'recordedAt': 録音日時（JST）,
                'duration_sec': 録音時間（秒）,
                'group_name': グループ名
            }
    """
    discussions: List[Dict[str, str]] = []
    found_ids = set()
    start_time = time.time()
    jst = pytz.timezone('Asia/Tokyo')
    
    while True:
        for discussion in hy_client.get_discussions(course_id):
            if discussion.id not in found_ids:
                found_ids.add(discussion.id)
                
                # UTCの日時をJSTに変換
                utc_time = discussion.recordedAt
                if isinstance(utc_time, str):
                    utc_time = datetime.fromisoformat(utc_time.replace('Z', '+00:00'))
                
                if utc_time.tzinfo is None:
                    utc_time = pytz.utc.localize(utc_time)
                jst_time = utc_time.astimezone(jst)
                
                discussion_info = {
                    'id': discussion.id,
                    'status': discussion.status,
                    'topic': discussion.topic,
                    'comment': discussion.comment,
                    'recordedAt': jst_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
                    'duration_sec': discussion.duration_sec,
                    'group_name': discussion.group_name
                }
                discussions.append(discussion_info)
                print(f"Found discussion: {discussion.id}")
        
        if time.time() - start_time > timeout:
            print(f"Timeout reached after {timeout} seconds")
            break
        
        if len(found_ids) == len(discussions):
            print("All discussions have been retrieved")
            break
    
    discussions.sort(key=lambda x: datetime.strptime(x['recordedAt'], '%Y-%m-%d %H:%M:%S %Z'), reverse=True)
    return discussions

def get_discussion_texts(
    hy_client: hylable.HDClient,
    discussion_ids: List[str]
) -> List[Dict[str, Union[str, List[str]]]]:
    """
    指定されたディスカッションIDのリストに対応する音声認識結果を取得します。

    Args:
        hy_client (hylable.HDClient): Hylableクライアントインスタンス
        discussion_ids (List[str]): ディスカッションIDのリスト

    Returns:
        List[Dict[str, Union[str, List[str]]]]: 各ディスカッションのIDとテキストのリストを含む辞書のリスト
    """
    results: List[Dict[str, Union[str, List[str]]]] = []
    for discussion_id in discussion_ids:
        discussion = hy_client.get_discussion(discussion_id)
        metadatas = hy_client.get_asr(discussion)
        texts: List[str] = [item['text'] for item in metadatas]
        results.append({"discussion_id": discussion_id, "texts": texts})
    return results

def get_single_discussion_text(
    hy_client: hylable.HDClient,
    discussion_id: str
) -> Dict[str, Union[str, List[str]]]:
    """
    指定されたディスカッションIDの音声認識結果を取得します。

    Args:
        hy_client (hylable.HDClient): Hylableクライアントインスタンス
        discussion_id (str): ディスカッションID

    Returns:
        Dict[str, Union[str, List[str]]]: ディスカッションIDとテキストのリストを含む辞書。
        エラーが発生した場合はNone
    """
    try:
        discussion = hy_client.get_discussion(discussion_id)
        metadatas = hy_client.get_asr(discussion)
        texts: List[str] = [item['text'] for item in metadatas]
        return {"discussion_id": discussion_id, "texts": texts}
    except IndexError as e:
        print(f"ディスカッション {discussion_id} の処理中にインデックスエラーが発生しました: {str(e)}")
        return None
    except Exception as e:
        print(f"ディスカッション {discussion_id} の処理中にエラーが発生しました: {str(e)}")
        return None

# -----
if __name__ == "__main__":
    # courseIDの指定
    course_id: str = "crs_89881258-9606-4d85-86cb-ad514df18c1f"
    
    output_dir = Path(f"./{course_id}")
    output_dir.mkdir(parents=True, exist_ok=True)  # ディレクトリが存在しない場合は作成

    # すべてのディスカッションIDを取得
    print("=== すべてのディスカッションの取得 ===")
    all_discussions: List[Dict[str, str]] = get_all_discussion_ids(hy_client, course_id, timeout=30)
    print(f"\ncourseID内に検出されたディスカッションの総数: {len(all_discussions)}")
    print("\n検出されたディスカッションの詳細:")
    print("\n" + "="*50 + "\n")
    
    print("=== すべてのディスカッションの情報 ===")
    if all_discussions:
        for discussion in tqdm(all_discussions, desc="Processing discussions"):
 
            print("\n=== ディスカッションの音声認識結果 ===")
            print(f"ID: {discussion['id']}")
            topic = "topic未設定"
            if discussion['topic']:
                print(f"トピック: {discussion['topic']}")
                topic = discussion['topic'].replace('/', '／')
            group_name = "group未設定"
            if discussion['group_name']:
                print(f"グループ名: {discussion['group_name']}")
                group_name = discussion['group_name']
            
            result = get_single_discussion_text(hy_client, discussion['id'])
            if result is None:
                print(f"ディスカッション {discussion['id']} をエラーのためスキップします")
                continue
            if result['texts']:
                # print("\n音声認識テキスト:")
                # for text in result['texts']:
                #     print(text)
                dt = datetime.strptime(discussion['recordedAt'], "%Y-%m-%d %H:%M:%S JST")
                formatted_date = dt.strftime("%Y%m%d_%H%M%S")
                filename = f"{formatted_date}({seconds_to_time_format(discussion['duration_sec'])})_{discussion['id']}_{topic}_{group_name}.asr.txt"
                with open(output_dir / filename, 'a', encoding='utf-8') as file:
                    file.write('\n'.join(result['texts']) + '\n')
            else:
                print("\n音声認識テキストはありません")
    print("\n" + "="*50 + "\n処理が完了しました")

# -------------------------------------------------    
#    # 最初のディスカッションの音声認識結果を取得
#    if all_discussions:
#        first_discussion = all_discussions[0]
#        print("\n=== 最新のディスカッションの音声認識結果 ===")
#        print(f"ID: {first_discussion['id']}")
#        print(f"グループ名: {first_discussion['group_name'] if first_discussion['group_name'] else '未設定'}")
#        if first_discussion['topic']:
#            print(f"トピック: {first_discussion['topic']}")
#        result = get_single_discussion_text(hy_client, first_discussion['id'])
#        if result['texts']:
#            print("\n音声認識テキスト:")
#            for text in result['texts']:
#                print(text)
#        else:
#            print("\n音声認識テキストはありません")
#    # 区切り線
#    print("\n" + "="*50 + "\n")
# -------------------------------------------------
#    # 録音中のディスカッションIDを取得
#    print("=== 録音中のディスカッションの取得 ===")
#    recording_discussion_ids: List[str] = get_recording_discussion_ids(hy_client, course_id, max_discussions=10, timeout=30)
#    print(f"\n録音中のディスカッションの総数: {len(recording_discussion_ids)}")
#    # 録音中のディスカッションの情報を表示
#    print("\n録音中のディスカッションの詳細:")
#    for i, disc_id in enumerate(recording_discussion_ids, 1):
#        disc_info = next((d for d in all_discussions if d['id'] == disc_id), None)
#        if disc_info:
#            print(f"\n{i}. ディスカッション情報:")
#            print(f"   ID: {disc_info['id']}")
#            print(f"   状態: {disc_info['status']}")
#            print(f"   録音日時: {disc_info['recordedAt']}")
#            print(f"   録音時間: {seconds_to_time_format(disc_info['duration_sec'])}")
#            print(f"   グループ名: {disc_info['group_name'] if disc_info['group_name'] else '未設定'}")
#            if disc_info['topic']:
#                print(f"   トピック: {disc_info['topic']}")
#            else:
#                print("   トピック: 未設定")
#            if disc_info['comment']:
#                print(f"   コメント: {disc_info['comment']}")
#            else:
#                print("   コメント: なし")
#    # 区切り線
#    print("\n" + "="*50 + "\n")
#    # 録音中のディスカッションの音声認識結果を取得
#    print("=== 音声認識結果の取得 ===")
#    results = get_discussion_texts(hy_client, recording_discussion_ids)
#    # 音声認識結果の表示
#    print("\n音声認識結果:")
#    for result in results:
#        # 対応するディスカッション情報を取得
#        disc_info = next((d for d in all_discussions if d['id'] == result['discussion_id']), None)
#        if disc_info:
#            print(f"\nDiscussion ID: {result['discussion_id']}")
#            print(f"グループ名: {disc_info['group_name'] if disc_info['group_name'] else '未設定'}")
#            if disc_info['topic']:
#                print(f"トピック: {disc_info['topic']}")
#            print("\nTexts:")
#            for text in result['texts']:
#                print(text)
#            print()
# -------------------------------------------------   

    # # 録音中のディスカッションIDを取得
    # print("=== 指定したID範囲のディスカッションの取得 ===")

    # if all_discussions:
    #     for i in range(109, 154):  # 97から153まで（154は含まない）
    #         discussion = all_discussions[i]

    #         print("\n=== ディスカッションの音声認識結果 ===")
    #         print(f"ID: {discussion['id']}")
    #         print(f"グループ名: {discussion['group_name'] if discussion['group_name'] else '未設定'}")
    #         if discussion['topic']:
    #             print(f"トピック: {discussion['topic']}")
                
    #         result = get_single_discussion_text(hy_client, discussion['id'])
    #         if result['texts']:
    #             # print("\n音声認識テキスト:")
    #             # for text in result['texts']:
    #             #     print(text)
    #             with open('result.txt', 'a', encoding='utf-8') as file:
    #                 file.write('\n'.join(result['texts']) + '\n')
    #         else:
    #             print("\n音声認識テキストはありません")
