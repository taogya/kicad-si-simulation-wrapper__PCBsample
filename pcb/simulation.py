import glob
from time import sleep
import subprocess


# メイン処理


def main():
    # 各ネット設定ファイルごとに処理
    for sim_dir in glob.glob("slices/*"):
        # シミュレーション実行
        subprocess.run(
            args=["gerber2ems", "-a", "--export-field", "-d"],
            cwd=sim_dir)
        sleep(1)  # 1秒待機


if __name__ == "__main__":
    main()
