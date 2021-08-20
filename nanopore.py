"""
Preprocessing for nanopore files to bring it into a format that can be accepted
by the human-removal pipeline.
"""

from pathlib import Path

import shlex
import argh


def is_dir_gzipped(directory: str) -> bool:
    """
    Check if the all the files in directory have a '.gz' extension
    """
    files = Path(directory).glob("**")
    if not files:
        return False
    files = filter(lambda x: x.is_file(), files)
    for f in files:
        if f.suffix != ".gz":
            return False
    return True


def concat_files_cmd(directory: str, out_file: str):
    """
    Return the commands to concat files in directory into out_file
    """
    files = Path(directory).glob("*")
    if not files:
        return False
    files = filter(lambda x: x.is_file(), files)
    files = map(str, files)
    cmds = list()
    if is_dir_gzipped(directory):
        for f in files:
            cmds.append(f"cat {shlex.quote(f)} >> {shlex.quote(out_file)}")
    else:
        for f in files:
            cmds.append(f"cat {shlex.quote(f)} | gzip -c >> {shlex.quote(out_file)}")
    return cmds


def nanopore_notmultiplexed_preprocess(input_dir: str, output_dir: str):
    """
    Return list of list of commands to execute to bring a
    non-multiplexed (single sample) nanopore run into a format
    that can be accepted by the preprocessing pipeline
    """
    input_dir = Path(input_dir)
    if not input_dir.is_dir():
        return False
    extension = ".fastq.gz"
    output_file = str(Path(output_dir) / ("nanopore_sample" + extension))
    cmds = [concat_files_cmd(input_dir, output_file)]
    return cmds


# single dir not multiplexed gzipped:
# /media/grid0/Ngon_SureSelect_342UB/no_sample/20210722_0850_X3_FAQ54593_c38f4b52/fastq_pass/
# multiplexed gzipped
# /media/grid0/DFB_R_15/no_sample/20210525_1816_X5_FAP94036_c8c034c5/fastq_pass/


def nanopore_multiplexed_preprocess(input_dir: str, output_dir: str):
    """
    Return list of list of commands to execute to bring a
    multiplexed (many samples) nanopore run into a format
    that can be accepted by the preprocessing pipeline

    This assumes that the barcode directories start with
    "barcode"
    """
    input_dir = Path(input_dir)
    if not input_dir.is_dir():
        return False

    cmds = list()
    for barcode_dir in input_dir.glob("*"):
        if not barcode_dir.is_dir():
            continue
        if str(barcode_dir.name)[0:7] != "barcode":
            continue

        extension = ".fastq.gz"

        output_file = str(Path(output_dir) / barcode_dir.name) + extension
        cmds.append(concat_files_cmd(barcode_dir, output_file))

    return cmds


if __name__ == "__main__":
    argh.dispatch_commands(
        [
            is_dir_gzipped,
            concat_files_cmd,
            nanopore_multiplexed_preprocess,
            nanopore_notmultiplexed_preprocess,
        ]
    )
