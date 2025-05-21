from si_wrapper.create_settings import main as settings_main
from si_wrapper.generate_slices import main as slice_main
import os
import shutil
import glob
import json
from time import sleep


def edit_json_file(file,
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

        data["board_offset"]["top"] = board_offset__top
        data["board_offset"]["bottom"] = board_offset__bottom
        data["board_offset"]["left"] = board_offset__left
        data["board_offset"]["right"] = board_offset__right
        data["included_pads"] = included_pads
        data["excluded_pads"] = excluded_pads
        data["hidden_pads"]["designated_net"] = hidden_pads__designated_net
        data["hidden_pads"]["other_nets"] = hidden_pads__other_nets
        data["neighbouring_nets"]["in_use"] = neighbouring_nets__in_use
        data["neighbouring_nets"]["offset"] = neighbouring_nets__offset
        data["neighbouring_nets"]["common_points"] = neighbouring_nets__common_points
        data["neighbouring_nets"]["netlist"] = neighbouring_nets__netlist

    with open(file, "w") as fp:
        json.dump(data, fp, indent=4)


def main():
    shutil.rmtree("net_configs", ignore_errors=True)
    shutil.rmtree("slices", ignore_errors=True)
    os.mkdir("net_configs")
    settings_main("init.json", "net_configs")
    included_pads_dict = {
        "RF1.json": ["J1", "AE1"],
        "RF2.json": ["J2", "AE2"],
    }
    for file in glob.glob("net_configs/*.json"):
        included_pads = included_pads_dict.get(os.path.basename(file), [])
        edit_json_file(file,
                       board_offset__top=1000,
                       board_offset__bottom=1000,
                       board_offset__left=1000,
                       board_offset__right=1000,
                       included_pads=included_pads,
                       hidden_pads__designated_net=False,
                       hidden_pads__other_nets=False,
                       neighbouring_nets__in_use=False)
        slice_main(file)
        sleep(1)


if __name__ == "__main__":
    main()
