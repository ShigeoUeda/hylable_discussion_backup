# Hylable Discussion ライブラリ

# 各関数の主な用途

- get_recording_discussion_ids: 録音中のディスカッションのIDのみを取得
- get_discussion_ids: 指定した数のディスカッションIDを取得
- get_all_discussion_ids: すべてのディスカッションの詳細情報（ID、状態、トピック、コメント、時間など）を取得
- get_discussion_texts: 複数のディスカッションIDに対する音声認識結果を一括取得
- get_single_discussion_text: 単一のディスカッションIDに対する音声認識結果を取得
- seconds_to_time_format: ユーティリティ関数として、秒数を日本語の時分秒形式に変換

# git cloneの方法

```sh
git clone https://github.com/ShigeoUeda/discussion_corpus.git
```

# git clone後の設定

以下の様にして仮想環境の設定、ライブラリのインストールを行う。

```sh
cd discussion_corpus
#仮想環境の設定・有効化
python -m venv venv
source ./venv/bin/activate
#ライブラリのインストール
pip install -r requirements.txt
pip install hylable-0.7.0-py3-none-any.whl
```

【注意】：**~/.hylable/config**の設定が必須です

# 実行方法

```sh
python hylable_processing.py
```

# ライブラリとして使用

以下をPythonファイルの冒頭に使用の用途に応じて追加すること。

```python
from hylable_processing import (
    get_recording_discussion_ids, # 録音中のディスカッションIDを取得
    get_discussion_ids,           # 指定数のディスカッションIDを取得（録音状態問わず）
    get_all_discussion_ids,       # すべてのディスカッションの詳細情報を取得
    get_discussion_texts,         # 複数のディスカッションの音声認識結果を取得
    get_single_discussion_text,   # 単一のディスカッションの音声認識結果を取得
    seconds_to_time_format        # 秒数を時分秒形式に変換
)
```

# 使用サンプル

**hylable_processing.py**の__main__部分に使い方があります。
