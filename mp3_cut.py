#!/usr/bin/env python3
"""
MP3 時間指定切り出しツール
JSONファイルから設定を読み込み、FFmpegで音声を切り出す
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any


def parse_time_to_seconds(time_str: str) -> float:
    """
    時刻文字列を秒数(float)に変換
    対応形式: "秒数" / "mm:ss" / "hh:mm:ss"
    
    Args:
        time_str: 時刻文字列
    
    Returns:
        秒数(float)
    
    Raises:
        ValueError: 不正な時刻形式の場合
    """
    time_str = str(time_str).strip()
    
    # 秒数のみの場合（数値として解釈可能）
    try:
        return float(time_str)
    except ValueError:
        pass
    
    # コロン区切りの場合
    parts = time_str.split(':')
    
    if len(parts) == 2:
        # mm:ss 形式
        try:
            minutes = int(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        except ValueError:
            raise ValueError(f"Invalid time format: {time_str}")
    
    elif len(parts) == 3:
        # hh:mm:ss 形式
        try:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        except ValueError:
            raise ValueError(f"Invalid time format: {time_str}")
    
    else:
        raise ValueError(f"Invalid time format: {time_str}")


def load_config(config_path: str) -> Dict[str, Any]:
    """
    JSONファイルから設定を読み込む
    
    Args:
        config_path: JSONファイルのパス
    
    Returns:
        設定辞書
    
    Raises:
        FileNotFoundError: ファイルが存在しない場合
        json.JSONDecodeError: JSON形式が不正な場合
        ValueError: 必須項目が不足している場合
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 必須項目の検証
    if 'source' not in config:
        raise ValueError("Missing required field: 'source'")
    
    if 'segments' not in config:
        raise ValueError("Missing required field: 'segments'")
    
    if not isinstance(config['segments'], list):
        raise ValueError("'segments' must be a list")
    
    if len(config['segments']) == 0:
        raise ValueError("'segments' cannot be empty")
    
    # 各セグメントの検証
    for i, segment in enumerate(config['segments']):
        if 'start' not in segment:
            raise ValueError(f"Segment {i}: Missing 'start' field")
        if 'end' not in segment:
            raise ValueError(f"Segment {i}: Missing 'end' field")
        if 'output' not in segment:
            raise ValueError(f"Segment {i}: Missing 'output' field")
    
    return config


def get_ffmpeg_executable() -> str:
    """
    imageio-ffmpegからFFmpegバイナリのパスを取得
    
    Returns:
        FFmpeg実行ファイルの絶対パス
    
    Raises:
        ImportError: imageio-ffmpegがインストールされていない場合
        RuntimeError: FFmpegバイナリの取得に失敗した場合
    """
    try:
        import imageio_ffmpeg
    except ImportError:
        raise ImportError(
            "imageio-ffmpeg is not installed. "
            "Please install it with: pip install imageio-ffmpeg"
        )
    
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    if not ffmpeg_exe:
        raise RuntimeError("Failed to get FFmpeg executable from imageio-ffmpeg")
    
    return ffmpeg_exe


def cut_segment(ffmpeg_exe: str, source: str, start: float, end: float, output: str) -> bool:
    """
    FFmpegを使用してMP3ファイルから指定範囲を切り出す
    
    Args:
        ffmpeg_exe: FFmpeg実行ファイルのパス
        source: 入力MP3ファイルのパス
        start: 開始時刻（秒）
        end: 終了時刻（秒）
        output: 出力ファイルのパス
    
    Returns:
        成功時True、失敗時False
    """
    # FFmpegコマンドの構築
    cmd = [
        ffmpeg_exe,
        '-ss', str(start),
        '-to', str(end),
        '-i', source,
        '-map_metadata', '-1',  # 全メタデータを削除
        '-vn',  # 動画ストリームを無効化
        '-c', 'copy',  # 再エンコードなし
        '-y',  # 上書き確認なし
        output
    ]
    
    try:
        print(f"  Processing: {output} (start={start}s, end={end}s)")
        
        # FFmpegを実行
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            print(f"  ✗ Failed to cut segment: {output}")
            print(f"    Error: {result.stderr}")
            return False
        
        print(f"  ✓ Successfully created: {output}")
        return True
        
    except Exception as e:
        print(f"  ✗ Exception occurred: {e}")
        return False


def process_segments(config: Dict[str, Any], ffmpeg_exe: str) -> None:
    """
    全セグメントを順次処理
    
    Args:
        config: 設定辞書
        ffmpeg_exe: FFmpeg実行ファイルのパス
    """
    source = config['source']
    segments = config['segments']
    
    # 入力ファイルの存在確認
    source_path = Path(source)
    if not source_path.exists():
        print(f"Error: Source file not found: {source}")
        sys.exit(1)
    
    print(f"Source: {source}")
    print(f"Total segments: {len(segments)}\n")
    
    success_count = 0
    failed_count = 0
    
    # 各セグメントを処理
    for i, segment in enumerate(segments, 1):
        print(f"[{i}/{len(segments)}]")
        
        try:
            # 時刻をパース
            start_seconds = parse_time_to_seconds(segment['start'])
            end_seconds = parse_time_to_seconds(segment['end'])
            
            # 時刻の妥当性チェック
            if start_seconds >= end_seconds:
                print(f"  ✗ Invalid time range: start ({start_seconds}s) >= end ({end_seconds}s)")
                failed_count += 1
                continue
            
            # 切り出し処理
            success = cut_segment(
                ffmpeg_exe,
                source,
                start_seconds,
                end_seconds,
                segment['output']
            )
            
            if success:
                success_count += 1
            else:
                failed_count += 1
                
        except ValueError as e:
            print(f"  ✗ Time parse error: {e}")
            failed_count += 1
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            failed_count += 1
        
        print()
    
    # 結果サマリー
    print("=" * 50)
    print(f"Completed: {success_count} succeeded, {failed_count} failed")
    print("=" * 50)


def main():
    """メイン処理"""
    # 引数チェック
    if len(sys.argv) != 2:
        print("Usage: mp3_cut.py <config.json>")
        sys.exit(1)
    
    config_path = sys.argv[1]
    
    try:
        # 設定ファイルの読み込み
        print("Loading configuration...")
        config = load_config(config_path)
        
        # FFmpegバイナリの取得
        print("Getting FFmpeg executable...")
        ffmpeg_exe = get_ffmpeg_executable()
        print(f"FFmpeg: {ffmpeg_exe}\n")
        
        # セグメント処理
        process_segments(config, ffmpeg_exe)
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ImportError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
