import os
import sys
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor
from collections import defaultdict

# 対象とする拡張子
EXTENSIONS = {
    # 標準画像
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff',
    # RAWフォーマット
    '.arw',  # SONY
    '.cr2', '.cr3',  # Canon
    '.nef',  # Nikon
    '.orf',  # Olympus
    '.raf',  # Fujifilm
    '.dng',  # Adobe / Digital Negative
    '.rw2'   # Panasonic
}

# ファイルのMD5ハッシュ値を計算
# @returns {ファイルパス, ハッシュ値}
def calculate_hash(file_path):
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            # 8KB単位で読み込み
            for chunk in iter(lambda: f.read(8192), b""):
                hash_md5.update(chunk)
        return str(file_path), hash_md5.hexdigest()
    except Exception as e:
        return str(file_path), None

# メイン処理
# @returns  none
def main():
    # コマンドライン引数解析
    parser = argparse.ArgumentParser(description="全階層の重複画像をチェックします。")
    parser.add_argument("dir", help="対象ディレクトリのパス")
    args = parser.parse_args()

    target_dir = Path(args.dir)
    if not target_dir.is_dir():
        print(f"エラー: {target_dir} は有効なディレクトリではありません。")
        sys.exit(1)

    # 1. 全階層からファイルをリストアップ
    print(f"📂 全階層をスキャン中: {target_dir}")
    files = [
        p for p in target_dir.rglob('*') 
        if p.is_file()
        and not p.name.startswith('.') 
        and p.suffix.lower() in EXTENSIONS
    ]

    if not files:
        print("対象となる画像ファイルが見つかりませんでした。")
        return

    print(f"🔍 {len(files)} 枚のファイルをチェック中...")

    # 2. 並列処理でハッシュ計算
    results = defaultdict(list)
    with ProcessPoolExecutor() as executor:
        for path_str, file_hash in executor.map(calculate_hash, files):
            if file_hash:
                results[file_hash].append(path_str)

    # 3. 重複の抽出
    duplicates = {h: paths for h, paths in results.items() if len(paths) > 1}

    # 4. 結果の書き出し
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"result_{timestamp}.txt"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"--- 重複ファイルチェック結果 ({datetime.now()}) ---\n")
        f.write(f"対象ディレクトリ: {target_dir.absolute()}\n")
        f.write(f"スキャン総数: {len(files)}\n\n")

        if not duplicates:
            f.write("重複は見つかりませんでした。\n")
        else:
            f.write(f"重複グループ数: {len(duplicates)}\n\n")
            for i, (h, paths) in enumerate(duplicates.items(), 1):
                f.write(f"Group {i} (Hash: {h})\n")
                for path in paths:
                    f.write(f"  - {path}\n")
                f.write("\n")

    print(f"✨ 完了！結果を {output_file} に保存しました。")
    if duplicates:
        print(f"⚠️ {len(duplicates)} 組の重複が見つかりました。")

if __name__ == "__main__":
    main()