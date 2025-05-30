from si_wrapper.create_settings import main as settings_main
from si_wrapper.generate_slices import main as slice_main
import os
import shutil
import glob
import json
from time import sleep
import subprocess
import csv


def edit_net_config(file,
                    board_offset__top=1,
                    board_offset__bottom=1,
                    board_offset__left=1,
                    board_offset__right=1,
                    included_pads=[],
                    excluded_pads=[],
                    hidden_pads__designated_net=True,
                    hidden_pads__other_nets=True,
                    neighbouring_nets__in_use=True,
                    neighbouring_nets__offset=0.01,
                    neighbouring_nets__common_points=100,
                    neighbouring_nets__netlist=[]):
    with open(file, "r") as fp:
        data = json.load(fp)

        # ボードオフセットの設定
        data["board_offset"]["top"] = board_offset__top
        data["board_offset"]["bottom"] = board_offset__bottom
        data["board_offset"]["left"] = board_offset__left
        data["board_offset"]["right"] = board_offset__right
        # パッドの設定
        data["included_pads"] = included_pads
        data["excluded_pads"] = excluded_pads
        # 非表示パッドの設定
        data["hidden_pads"]["designated_net"] = hidden_pads__designated_net
        data["hidden_pads"]["other_nets"] = hidden_pads__other_nets
        # 近傍ネットの設定
        data["neighbouring_nets"]["in_use"] = neighbouring_nets__in_use
        data["neighbouring_nets"]["offset"] = neighbouring_nets__offset
        data["neighbouring_nets"]["common_points"] = neighbouring_nets__common_points
        data["neighbouring_nets"]["netlist"] = neighbouring_nets__netlist

    # 編集した内容をファイルに書き戻す
    with open(file, "w") as fp:
        json.dump(data, fp, indent=4)


def edit_simulation_settings(file,
                             frequency__start=200e6,
                             frequency__stop=4e9,
                             pixel_size=5,
                             max_steps=5e5,
                             via__filling_epsilon=1,
                             via__plating_thickness=50,
                             mesh__xy=50,
                             mesh__inter_layers=4,
                             mesh__margin__xy=200,
                             mesh__margin__z=200,
                             margin__xy=500,
                             margin__z=500):
    with open(file, "r") as fp:
        data = json.load(fp)
        # 周波数設定
        data["frequency"]["start"] = frequency__start
        data["frequency"]["stop"] = frequency__stop
        # ピクセルサイズ設定
        data["pixel_size"] = pixel_size
        # 最大ステップ数設定
        data["max_steps"] = max_steps
        # ビアの設定
        data["via"]["filling_epsilon"] = via__filling_epsilon
        data["via"]["plating_thickness"] = via__plating_thickness
        # メッシュの設定
        data["mesh"]["xy"] = mesh__xy
        data["mesh"]["inter_layers"] = mesh__inter_layers
        data["mesh"]["margin"]["xy"] = mesh__margin__xy
        data["mesh"]["margin"]["z"] = mesh__margin__z
        # マージンの設定
        data["margin"]["xy"] = margin__xy
        data["margin"]["z"] = margin__z

    # 編集した内容をファイルに書き戻す
    with open(file, "w") as fp:
        json.dump(data, fp, indent=4)


def main():
    # 既存ディレクトリの削除
    shutil.rmtree("net_configs", ignore_errors=True)
    shutil.rmtree("slices", ignore_errors=True)
    # ディレクトリ作成
    os.mkdir("net_configs")
    # 設定ファイル生成
    settings_main("init.json", "net_configs")
    # 各ネットごとのパッド指定
    included_pads_dict = {
        "RF1.json": ["J1", "AE1"],
        "RF2.json": ["J2", "AE2"],
    }
    # 各ネット設定ファイルごとに処理
    for file in glob.glob("net_configs/*.json"):
        included_pads = included_pads_dict.get(os.path.basename(file), [])

        # JSONファイル編集
        edit_net_config(file,
                        board_offset__top=50,
                        board_offset__bottom=50,
                        board_offset__left=50,
                        board_offset__right=50,
                        included_pads=included_pads,
                        hidden_pads__designated_net=False,
                        hidden_pads__other_nets=False,
                        neighbouring_nets__in_use=False)

        # スライス生成
        slice_main(file)

        # gerber生成コマンド実行
        subprocess.run(
            args=["kmake", "gerber", "-xe"],
            cwd=os.path.join("slices", os.path.basename(file).replace(".json", ""))
        )

        # png生成コマンド実行
        subprocess.run(
            args=["si-wrapper", "gerber2png"],
            cwd=os.path.join("slices", os.path.basename(file).replace(".json", ""))
        )

        # pnp生成コマンド実行
        subprocess.run(
            args=["kmake", "pnp", "-t"],
            cwd=os.path.join("slices", os.path.basename(file).replace(".json", ""))
        )

        # stackup生成コマンド実行
        subprocess.run(
            args=["kmake", "stackup-export"],
            cwd=os.path.join("slices", os.path.basename(file).replace(".json", ""))
        )

        # fabディレクトリ内のcsvファイルを処理
        for csv_file in glob.glob(os.path.join("slices", os.path.basename(file).replace(".json", ""), "fab", "*.csv")):
            write_data = []
            with open(csv_file, "r") as fp:
                reader = csv.reader(fp)
                write_data.append(next(reader))  # ヘッダー行
                for row in reader:
                    if row[0].startswith("SP"):  # "SP"で始まる行のみ抽出
                        write_data.append(row)
            with open(csv_file, "w") as fp:
                writer = csv.writer(fp)
                writer.writerows(write_data)

        # netinfo.jsonは使わないのでリネーム
        os.rename(
            os.path.join("slices", os.path.basename(file).replace(".json", ""), "netinfo.json"),
            os.path.join("slices", os.path.basename(file).replace(".json", ""), "netinfo.json.bak")
        )

        # シミュレーション設定ファイルの編集
        edit_simulation_settings(
            os.path.join("slices", os.path.basename(file).replace(".json", ""), "simulation.json"),
            frequency__start=1e9,
            frequency__stop=20e9,
            pixel_size=10,
            max_steps=8096,
            via__filling_epsilon=1,
            via__plating_thickness=50,
            mesh__xy=50,
            mesh__inter_layers=4,
            mesh__margin__xy=200,
            mesh__margin__z=200,
            margin__xy=500,
            margin__z=500
        )

        # 1秒待機
        sleep(1)


if __name__ == "__main__":
    main()
