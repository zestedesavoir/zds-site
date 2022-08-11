import argparse
import pathlib
import os

import cairosvg


def convert_folder_to_svg(src_folder: pathlib.Path, dst_folder: pathlib.Path) -> int:
    """
    Convert all SVGs from src_folder into PNGs and write them in dst_folder.
    Create dst_folder if needed.
    Existing files in dst_fodler are overwritten.
    Return the number of converted files.
    """
    src_files = src_folder.rglob("*.svg")
    os.makedirs(dst_folder, exist_ok=True)
    converted_file_count = 0
    for src_file in src_files:
        dst_file = dst_folder / f"{src_file.stem}.png"
        cairosvg.svg2png(url=src_file.as_posix(), write_to=dst_file.as_posix())
        converted_file_count += 1
    return converted_file_count


def get_cli_args():
    """Get arguments from the CLI."""

    # Build parser
    parser = argparse.ArgumentParser(description="Convert a folder of SVG files to PNG")
    parser.add_argument("source", help="Folder containing the SVG files to be converted")
    parser.add_argument("destination", help="Folder in which the PNG files are written")

    # Parse
    raw_args = parser.parse_args()
    processed_args = {
        "source": pathlib.Path(raw_args.source),
        "destination": pathlib.Path(raw_args.destination),
    }

    return processed_args


if __name__ == "__main__":
    args = get_cli_args()
    file_count = convert_folder_to_svg(args["source"], args["destination"])
    print(f"{__file__}: {file_count} files converted.")
