# MP3 時間指定切り出しツール

## 概要
長尺 MP3 ファイル（約 1 時間など）から、指定した時間範囲を切り出し、
音質・ビットレートを維持したまま MP3 として出力する CLI ツール。

- 再エンコードは行わない
- メタデータはすべて削除する
- 1つの入力ファイルから複数範囲を一括で切り出せる
- ホスト PC への FFmpeg 事前インストールは不要
- ツールの挙動は **JSON 定義のみ** によって決定される

---

## 技術スタック
- Python 3.x
- imageio-ffmpeg
  - FFmpeg バイナリをツール側で自動取得・内包
  - 取得した FFmpeg を外部コマンドとして使用

---

## CLI 仕様
CLI 引数は **JSON ファイルのパスのみ** を受け取る。

```bash
mp3_cut.py config.json
```

* 処理内容・挙動はすべて `config.json` に定義する
* CLI オプションは追加しない

---

## 入力仕様（JSON）

### JSON 構造
```json
{
  "source": "/path/to/input.mp3",
  "segments": [
    {
      "start": "10:00",
      "end": "15:30",
      "output": "part1.mp3"
    },
    {
      "start": "30:00",
      "end": "42:10",
      "output": "part2.mp3"
    }
  ]
}
```

### 各項目の意味

#### ルート要素
* `source`
  * 切り出し元となる MP3 ファイルのパス
* `segments`
  * 切り出し定義の配列

#### segments 要素
* `start`
  * 切り出し開始時刻
  * 指定形式：`mm:ss` / `hh:mm:ss` / 秒数
* `end`
  * 切り出し終了時刻
  * 指定形式：`mm:ss` / `hh:mm:ss` / 秒数
* `output`
  * 出力される MP3 ファイル名（パス指定可）

---

## 処理仕様
* JSON ファイルを読み込み、内容に基づいて処理を決定する
* 各 `segments` を順次処理する
* 同一入力ファイルから複数回の切り出しを行う
* 1セグメントの失敗が他セグメントに影響しない設計とする
* 時刻指定は内部で秒数（float）に正規化して扱う
* FFmpeg バイナリは imageio-ffmpeg を通じて取得したものを使用する

---

## FFmpeg 実行方針

### 基本コマンド構成
```bash
<ffmpeg_exe> \
  -ss <start> \
  -to <end> \
  -i <source> \
  -map_metadata -1 \
  -vn \
  -c copy \
  <output>
```

※ `<ffmpeg_exe>` は imageio-ffmpeg により取得した FFmpeg 実行ファイルの絶対パス

### 方針
* `-c copy` により再エンコードを行わない
* `-map_metadata -1` により全メタデータを削除する
* 音声ストリームのみを出力対象とする

---

## 補足事項
* 初回実行時に imageio-ffmpeg が FFmpeg バイナリを自動ダウンロードする
* ダウンロード後はホスト環境に依存せず同一挙動で実行可能
