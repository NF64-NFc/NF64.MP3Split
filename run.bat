@echo off
setlocal enabledelayedexpansion

REM MP3 時間指定切り出しツール実行バッチ
REM このバッチファイルと config.json が同じディレクトリにあることを前提とします

cd /d "%~dp0"

echo.
echo ========================================
echo MP3 時間指定切り出しツール
echo ========================================
echo.

REM Pythonの確認
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python が見つかりません
    echo         Python 3.x をインストールしてください
    pause
    exit /b 1
)

REM 依存パッケージのインストール確認
echo [INFO] 依存パッケージをチェック中...
pip show imageio-ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] imageio-ffmpeg をインストール中...
    if exist requirements.txt (
        pip install -r requirements.txt
    ) else (
        pip install imageio-ffmpeg>=0.4.9
    )
    if !errorlevel! neq 0 (
        echo [ERROR] パッケージのインストールに失敗しました
        pause
        exit /b 1
    )
)

REM config.json の確認
if not exist config.json (
    echo [ERROR] config.json が見つかりません
    echo         config.json を作成してください
    echo.
    echo 例: config.example.json を参照してください
    pause
    exit /b 1
)

echo [INFO] 処理を開始します...
echo.

REM mp3_cut.py を実行
python mp3_cut.py config.json
if !errorlevel! neq 0 (
    echo.
    echo [ERROR] 処理中にエラーが発生しました
    pause
    exit /b 1
)

echo.
echo ========================================
echo 処理が完了しました
echo ========================================
pause
