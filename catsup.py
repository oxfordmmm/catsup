#! /usr/bin/env python3
import collections
import copy
import csv
import json
import logging
import os
import pathlib
import shlex
import shutil
import subprocess
import sys
import uuid

import par_upload
import validate
import nanopore

cfg = None

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def read_cfg(cfg_file, cfg_file_example):
    if not pathlib.Path(cfg_file).exists():
        if pathlib.Path(cfg_file_example).exists():
            logging.info(f"{cfg_file} not found. Copying from {cfg_file_example}")
            shutil.copyfile(cfg_file_example, cfg_file)
            logging.info(
                f"Please edit {cfg_file} to make it work with your environment"
            )
            sys.exit(0)
        else:
            logging.error(
                f"Couldn't find config file ({cfg_file}) or config file example ({cfg_file_example})"
            )
            sys.exit(1)
    global cfg
    with open(cfg_file) as f:
        cfg = json.loads(f.read())
        if not validate.validate_config(cfg):
            logging.error(f"Config file ({cfg_file}) is not valid.")
            sys.exit(1)


read_cfg("config.json", "config.json-example")

in_csv_name = "inputs.csv"
out_csv_name = "sp3data.csv"
sample_guid_map_name = "sample_guid_map.csv"

in_fieldnames = [
    "index",
    "subindex",
    "sample_name",
    "sample_filename",
    "sample_file_extension",
    "sample_host",
    "sample_collection_date",
    "sample_country",
    "submission_title",
    "submission_description",
    "submitter_organisation",
    "submitter_email",
    "instrument_platform",
    "instrument_model",
    "instrument_flowcell",
]


sample_guid_map = dict()
guid_index = collections.defaultdict(int)


def make_example_entries(n, files, number_of_files_per_sample):
    ret = list()
    k = 0
    for i in range(1, n + 1):
        for j in range(1, number_of_files_per_sample + 1):
            if files:
                logging.debug(f"{i}, {j}, {k}")
                filename = files[k]
                k = k + 1
                sample_name = str(filename.name).split(".")[0]
            else:
                filename = f"in/P000{i}_{j}.fastq.gz"
                sample_name = f"P000{i}"

            tmp = [
                i,
                j,
                sample_name,
                filename,
                "fastq.gz",
                "Homo sapiens",
                "2020-01-30",
                "United Kingdom",
                "Bacteria infection study",
                "Bacteria infection study for drug resistance",
                "University of Oxford",
                "crookit@ndm.ox.ac.uk",
                "Illumina pair-ended sequencing",
                "Illumina HiSeq 4000",
                "96",
            ]
            yield {in_fieldnames[i]: tmp[i] for i, _ in enumerate(in_fieldnames)}
    return ret


out_fieldnames = copy.copy(in_fieldnames)
out_fieldnames.remove("sample_name")
out_fieldnames.insert(0, "submission_uuid4")
out_fieldnames.insert(1, "sample_uuid4")
out_fieldnames.append("original_file_md5")
out_fieldnames.append("original_file_sha1")
out_fieldnames.append("original_file_sha512")
out_fieldnames.append("clean_file_md5")
out_fieldnames.append("clean_file_sha1")
out_fieldnames.append("clean_file_sha512")


def hash_file(filename):
    hashmd5 = (
        subprocess.check_output(shlex.split(f"md5sum {filename}"))
        .strip()
        .split()[0]
        .decode()
    )
    hashsha1 = (
        subprocess.check_output(shlex.split(f"sha1sum {filename}"))
        .strip()
        .split()[0]
        .decode()
    )
    hashsha512 = (
        subprocess.check_output(shlex.split(f"sha512sum {filename}"))
        .strip()
        .split()[0]
        .decode()
    )
    return hashmd5, hashsha1, hashsha512


map_fieldnames = ["sample_name", "sample_uuid4", "original_file", "renamed_file"]


def step_msg(step, state, **kwargs):
    steps = {
        1: "user template",
        2: "prepare data",
        3: "nextflow pipeline",
        4: "s3 upload",
    }

    if state == "begin":
        logging.info(f"\n*** Preprocessing step: {steps[step]}\n")

    if state == "end":
        logging.info(f"\n*** Finished preprocessing step: {steps[step]}")
        if step + 1 in steps:
            logging.info(f"\n*** Next step: {steps[step+1]}\n")


def nanopore_prepare(submission_name):
    def api_begin():
        (pathlib.Path(submission_name) / ".step1.5-running").touch(exist_ok=True)
        unlink_missing_ok(pathlib.Path(submission_name) / ".step1.5-ok")
        unlink_missing_ok(pathlib.Path(submission_name) / ".step1.5-error")

    def api_error(err_dict):
        unlink_missing_ok(pathlib.Path(submission_name) / ".step1.5-running")
        unlink_missing_ok(pathlib.Path(submission_name) / ".step1.5-ok")
        with open(pathlib.Path(submission_name) / ".step1.5-error", "w") as f:
            f.write(json.dumps(err_dict))

    def api_success():
        unlink_missing_ok(pathlib.Path(submission_name) / ".step1.5-running")
        (pathlib.Path(submission_name) / ".step1.5-ok").touch(exist_ok=True)
        unlink_missing_ok(pathlib.Path(submission_name) / ".step1.5-error")

    api_begin()

    nanopore_variant = open(
        pathlib.Path(submission_name) / ".submission_variant"
    ).read()
    input_dir = open(pathlib.Path(submission_name) / ".submission_dir").read()

    if nanopore_variant:
        nanopore_output_dir = pathlib.Path(submission_name) / "nanopore_concated"
        nanopore_output_dir.mkdir(exist_ok=True)
        nanopore_cmds = list()

        if nanopore_variant == "multiplexed_v1":
            nanopore_cmds = nanopore.nanopore_multiplexed_preprocess(
                input_dir, str(nanopore_output_dir)
            )

        if nanopore_variant == "notmultiplexed_v1":
            nanopore_cmds = nanopore.nanopore_notmultiplexed_preprocess(
                input_dir, str(nanopore_output_dir)
            )

        if nanopore_variant == "dirfiles_v1":
            nanopore_cmds = nanopore.nanopore_dirfiles_preprocess(
                input_dir, str(nanopore_output_dir)
            )

        for cmds_list in nanopore_cmds:
            for cmd in cmds_list:
                logging.info(cmd)
                os.system(cmd)

    api_success()


def create_template(
    submission_name,
    args,
    number_of_files_per_sample,
    nanopore_variant="",
    api=False,
    trunc=False,
):
    step_msg(1, "begin")
    pathlib.Path(submission_name).mkdir(exist_ok=True)
    input_csv = pathlib.Path(submission_name) / in_csv_name
    if input_csv.exists() and not trunc:
        if api:
            return {"status": "error", "reason": "input_csv_exists"}
        else:
            logging.error(f"File {input_csv} exists. Won't overwrite.")
            sys.exit(1)

    if args:
        directory = pathlib.Path(args[0])
        if directory.exists():
            files = sorted(list(directory.glob("*")), key=lambda x: x.name)
            with open(input_csv, "w", newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=in_fieldnames)
                writer.writeheader()
                for row in make_example_entries(
                    len(files) // number_of_files_per_sample,
                    files,
                    number_of_files_per_sample,
                ):
                    writer.writerow(row)
        else:
            return {"status": "error", "reason": "files_dir_missing"}

    else:
        with open(input_csv, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=in_fieldnames)
            writer.writeheader()
            number_of_example_samples = cfg.get("number_of_example_samples", 4)
            for row in make_example_entries(
                number_of_example_samples, None, number_of_example_samples
            ):
                writer.writerow(row)

    logging.info(f"Created {input_csv}")
    logging.info("Edit the file to add your samples.")

    step_msg(1, "end")

    if api:
        return {"status": "success", "input_csv": input_csv}


def sample_name_to_guid(sample_name):
    """
    return sample uuid or create one if it doesn't exist
    """
    global sample_guid_map
    if sample_name not in sample_guid_map:
        sample_guid_map[sample_name] = str(uuid.uuid4())
    return sample_guid_map[sample_name]


def sample_uuid_to_index(sample_uuid4):
    """
    return how many times we've already seen the uuid
    """
    global guid_index
    guid_index[sample_uuid4] = guid_index[sample_uuid4] + 1
    return guid_index[sample_uuid4]


def new_sample_filename(
    sample_name, sample_filename, sample_file_extension, guid, index
):
    return guid + "_" + str(index) + "." + sample_file_extension


def rename_sample(sample_filename, renamed_filename, submission_name):
    i = pathlib.Path(sample_filename).absolute()
    (pathlib.Path(submission_name) / "pipeline_in").mkdir(exist_ok=True)
    o = pathlib.Path(submission_name) / "pipeline_in" / renamed_filename
    logging.info(f"{o} -> {i}")
    os.symlink(i, o)


def prepare_data(submission_name):
    global sample_guid_map
    sample_guid_map = dict()
    global guid_index
    guid_index = collections.defaultdict(int)

    def api_begin():
        (pathlib.Path(submission_name) / ".step2-running").touch(exist_ok=True)
        unlink_missing_ok(pathlib.Path(submission_name) / ".step2-ok")
        unlink_missing_ok(pathlib.Path(submission_name) / ".step2-error")

    def api_error(err_dict):
        unlink_missing_ok(pathlib.Path(submission_name) / ".step2-running")
        unlink_missing_ok(pathlib.Path(submission_name) / ".step2-ok")
        with open(pathlib.Path(submission_name) / ".step2-error", "w") as f:
            f.write(json.dumps(err_dict))

    def api_success():
        unlink_missing_ok(pathlib.Path(submission_name) / ".step2-running")
        (pathlib.Path(submission_name) / ".step2-ok").touch(exist_ok=True)
        unlink_missing_ok(pathlib.Path(submission_name) / ".step2-error")

    api_begin()
    step_msg(2, "begin")
    logging.info("Preparing data for pipeline")

    input_csv = pathlib.Path(submission_name) / in_csv_name

    if not pathlib.Path(input_csv).exists():
        api_error({"status": "failure", "reason": "inputs_csv_missing"})
        logging.error(f"File {input_csv} doesn't exists. Can't validate.")
        sys.exit(1)

    with open(input_csv, "r", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        if reader.fieldnames != in_fieldnames:
            logging.error(f"File {input_csv} has wrong header:")
            logging.error(f"Expected: {in_fieldnames}")
            logging.error(f"Received: {reader.fieldnames}")
            api_error({"status": "failure", "reason": "invalid_inputs_csv"})
            sys.exit(1)

        if not validate.validate_template(reader):
            api_error({"status": "failure", "reason": "invalid_inputs_csv"})
            logging.error("Couldn't validate template")
            sys.exit(-1)

    input_csv = pathlib.Path(submission_name) / in_csv_name
    sp3data_csv = pathlib.Path(submission_name) / "sp3data.csv"
    sample_map_csv = pathlib.Path(submission_name) / "sample_uuid_map.csv"

    with open(input_csv, "r") as infile, open(sp3data_csv, "w") as outfile, open(
        sample_map_csv, "w"
    ) as mapfile:
        reader = csv.DictReader(infile)
        writer1 = csv.DictWriter(outfile, fieldnames=out_fieldnames)
        writer1.writeheader()
        writer2 = csv.DictWriter(mapfile, fieldnames=map_fieldnames)
        writer2.writeheader()

        submission_uuid4 = str(uuid.uuid4())

        for row in reader:
            out = copy.copy(row)
            (
                out["original_file_md5"],
                out["original_file_sha1"],
                out["original_file_sha512"],
            ) = hash_file(out["sample_filename"])
            out["clean_file_md5"], out["clean_file_sha1"], out["clean_file_sha512"] = (
                "",
                "",
                "",
            )
            out["submission_uuid4"] = submission_uuid4
            out["sample_uuid4"] = sample_name_to_guid(out["sample_name"])
            guid_index_ = sample_uuid_to_index(out["sample_uuid4"])

            renamed_filename = new_sample_filename(
                out["sample_name"],
                out["sample_filename"],
                out["sample_file_extension"],
                out["sample_uuid4"],
                guid_index_,
            )

            rename_sample(out["sample_filename"], renamed_filename, submission_name)

            writer2.writerow(
                {
                    "sample_name": out["sample_name"],
                    "sample_uuid4": out["sample_uuid4"],
                    "original_file": row["sample_filename"],
                    "renamed_file": renamed_filename,
                }
            )
            del out["sample_name"]
            out["sample_filename"] = renamed_filename
            writer1.writerow(out)

    sp3data_csv = pathlib.Path(submission_name) / "sp3data.csv"
    sample_map_csv = pathlib.Path(submission_name) / "sample_uuid_map.csv"

    logging.info(f"Wrote sp3 submission data to: {sp3data_csv}")
    logging.info(f"Wrote sample file <-> uuid map to: {sample_map_csv}")

    step_msg(2, "end")

    api_success()


def process_csv(csv_filename):
    with open(csv_filename) as infile:
        reader = csv.DictReader(infile)
        data = list()
        for row in reader:
            data.append(copy.copy(row))

    with open(csv_filename, "w") as outfile:
        writer = csv.DictWriter(outfile, out_fieldnames)
        writer.writeheader()
        for row in data:
            yield writer, row


def make_clean_filename(sample_uuid4, subindex, sample_file_extension):
    return f"{sample_uuid4}_C{subindex}.{sample_file_extension}"


def hash_clean_files(submission_name):
    submission_uuid4 = None
    for writer, row in process_csv(f"{submission_name}/sp3data.csv"):
        submission_uuid4 = row["submission_uuid4"]
        directory = f"{submission_name}/upload/"
        filename = make_clean_filename(
            row["sample_uuid4"], row["subindex"], row["sample_file_extension"]
        )
        (
            row["clean_file_md5"],
            row["clean_file_sha1"],
            row["clean_file_sha512"],
        ) = hash_file(directory + "/" + filename)
        row["sample_filename"] = filename
        writer.writerow(row)
    return submission_uuid4


def unlink_missing_ok(p):
    try:
        p.unlink()
    except FileNotFoundError:
        pass


def run_pipeline(submission_name, number_of_files_per_sample):
    def api_begin():
        (pathlib.Path(submission_name) / ".step3-running").touch(exist_ok=True)
        unlink_missing_ok(pathlib.Path(submission_name) / ".step3-ok")
        unlink_missing_ok(pathlib.Path(submission_name) / ".step3-error")

    def api_error(err_dict):
        unlink_missing_ok(pathlib.Path(submission_name) / ".step3-running")
        unlink_missing_ok(pathlib.Path(submission_name) / ".step3-ok")
        with open(pathlib.Path(submission_name) / ".step3-error", "w") as f:
            f.write(json.dumps(err_dict))

    def api_success():
        unlink_missing_ok(pathlib.Path(submission_name) / ".step3-running")
        (pathlib.Path(submission_name) / ".step3-ok").touch(exist_ok=True)
        unlink_missing_ok(pathlib.Path(submission_name) / ".step3-error")

    api_begin()
    pipeline = cfg.get("pipeline", "catnip")
    pipeline_script = cfg.get("pipelines").get(pipeline).get("script")
    pipeline_image = cfg.get("pipelines").get(pipeline).get("image")
    pipeline_human_ref = cfg.get("pipelines").get(pipeline).get("kraken2_human_ref")
    container = cfg.get("container")
    nextflow_additional_params = cfg.get("nextflow_additional_params")

    ont_param = str()
    try:
        nanopore_variant = open(
            pathlib.Path(submission_name) / ".submission_variant"
        ).read()
        if (
            nanopore_variant == "multiplexed_v1"
            or nanopore_variant == "notmultiplexed_v1"
            or nanopore_variant == "dirfiles_v1"
        ):
            ont_param = "--sequencing ONT"
            pipeline_human_ref = (
                cfg.get("pipelines").get(pipeline).get("centrifuge_human_ref")
            )
            number_of_files_per_sample = 1

    except Exception:
        pass

    step_msg(3, "begin")
    logging.info(f"Running pipeline: {pipeline}")

    if number_of_files_per_sample == 2:
        nf_cmd = f"nextflow {pipeline_script} {nextflow_additional_params} --input_dir ../pipeline_in/ --read_pattern '*_{{1,2}}.fastq.gz' --paired true --output_dir ../upload -with-{container} {pipeline_image} --db {pipeline_human_ref}"
    if number_of_files_per_sample == 1:
        nf_cmd = f"nextflow {pipeline_script} {nextflow_additional_params} {ont_param} --input_dir ../pipeline_in/ --read_pattern '*_1.fastq.gz' --paired false --output_dir ../upload -with-{container} {pipeline_image} --db {pipeline_human_ref}"

    new_dir = f"{submission_name}/pipeline_run"
    pathlib.Path(new_dir).mkdir(exist_ok=True)
    logging.info(f"Changing directory to: {new_dir}")
    logging.info(f"Nextflow invocation: {nf_cmd}")

    try:
        subprocess.check_output(shlex.split(nf_cmd), cwd=str(new_dir))
    except subprocess.CalledProcessError as e:
        api_error(
            {
                "status": "failure",
                "reason": "nextflow_sucks",
                "python_exception": str(e),
            }
        )
        sys.exit(1)
    except Exception as e:
        api_error(
            {"status": "failure", "reason": "unknown_error", "python_exception": str(e)}
        )
        sys.exit(1)

    if not (pathlib.Path(submission_name) / "upload").is_dir():
        api_error({"status": "failure", "reason": "no_upload_dir"})
        sys.exit(1)
    if not list((pathlib.Path(submission_name) / "upload").glob("*")):
        api_error({"status": "failure", "reason": "empty_upload_dir"})
        sys.exit(1)

    try:
        nf_clean_cmd = "nextflow clean -f -k"
        subprocess.check_output(shlex.split(nf_clean_cmd), cwd=str(new_dir))
    except Exception as e:
        logging.error(e)

    api_success()
    step_msg(3, "end")


def upload_to_sp3(submission_name):
    def api_begin():
        (pathlib.Path(submission_name) / ".step4-running").touch(exist_ok=True)
        unlink_missing_ok(pathlib.Path(submission_name) / ".step4-ok")
        unlink_missing_ok(pathlib.Path(submission_name) / ".step4-error")

    def api_error(err_dict):
        unlink_missing_ok(pathlib.Path(submission_name) / ".step4-running")
        unlink_missing_ok(pathlib.Path(submission_name) / ".step4-ok")
        with open(pathlib.Path(submission_name) / ".step4-error", "w") as f:
            f.write(json.dumps(err_dict))

    def api_success():
        unlink_missing_ok(pathlib.Path(submission_name) / ".step4-running")
        (pathlib.Path(submission_name) / ".step4-ok").touch(exist_ok=True)
        unlink_missing_ok(pathlib.Path(submission_name) / ".step4-error")

    api_begin()
    step_msg(4, "begin")
    logging.info("Uploading to S3")

    try:
        with open(pathlib.Path(submission_name) / ".par_url") as f:
            par_url = f.read().strip()
    except Exception:
        par_url = None

    try:
        submission_uuid4 = hash_clean_files(submission_name)
    except Exception as e:
        api_error(
            {
                "status": "failure",
                "reason": "couldn't hash files",
                "more": {"error_exception_str": str(e)},
                "par_url": par_url,
                "files": [
                    str(x) for x in pathlib.Path(submission_name).glob("upload/*")
                ],
            }
        )
        sys.exit(1)

    s = pathlib.Path(f"{submission_name}/sp3data.csv")
    d = pathlib.Path(f"{submission_name}/upload/sp3data.csv")
    shutil.copy(s, d)

    bucket = cfg.get("upload").get("s3").get("bucket")

    if not par_url:
        par_url = cfg.get("upload").get("s3").get("par_url")
    if not bucket and not par_url:
        logging.error(
            "You need either an upload.s3.bucket key or an upload.s3.par_url key"
        )
        api_error({"status": "failure", "reason": "upload_misconfiguration"})
        sys.exit(1)

    if par_url:
        # upload to oracle s3 with preauthenticated request
        try:
            error = par_upload.upload_run(par_url, submission_name)
            if error:
                api_error(
                    {
                        "status": "failure",
                        "reason": "par_upload_failed",
                        "more": error,
                        "par_url": par_url,
                        "files": [
                            str(x)
                            for x in pathlib.Path(submission_name).glob("upload/*")
                        ],
                    }
                )
                sys.exit(1)

        except Exception as e:
            api_error(
                {
                    "status": "failure",
                    "reason": "par_upload_failed",
                    "more": {"error_exception_str": str(e)},
                    "par_url": par_url,
                    "files": [
                        str(x) for x in pathlib.Path(submission_name).glob("upload/*")
                    ],
                }
            )
            sys.exit(1)

    if bucket:
        # upload to bucket with s3cmd
        s3cmd_config = cfg.get("upload").get("s3").get("s3cmd-config")
        files = " ".join(
            [str(x) for x in pathlib.Path(f"{submission_name}/upload/").glob("*")]
        )
        s3cmd = f"s3cmd -c {s3cmd_config} put {files} {bucket}/{submission_uuid4}/"
        logging.info(f"s3cmd invocation: {s3cmd}")
        try:
            subprocess.check_output(shlex.split(s3cmd))
        except subprocess.CalledProcessError:
            api_error({"status": "failure", "reason": "s3cmd_failed"})
            sys.exit(1)
        logging.info(f"Uploaded files to: {bucket}/{submission_uuid4}")

    step_msg(4, "end")
    api_success()


def main():
    if len(sys.argv) <= 1:
        logging.error("Please pass a submission name as a first argument")
        sys.exit(1)
    submission_name = sys.argv[1]
    pathlib.Path(submission_name).mkdir(exist_ok=True)

    number_of_files_per_sample = int(cfg.get("number_of_files_per_sample"))
    input_csv = pathlib.Path(submission_name) / in_csv_name
    upload_dir = pathlib.Path(submission_name) / "upload"
    pipeline_in_dir = pathlib.Path(submission_name) / "pipeline_in"

    if upload_dir.exists():
        upload_to_sp3(submission_name)
    elif pipeline_in_dir.exists():
        run_pipeline(submission_name, number_of_files_per_sample)
    elif input_csv.exists():
        prepare_data(submission_name)
    else:
        create_template(submission_name, sys.argv[2:], number_of_files_per_sample)


if __name__ == "__main__":
    main()
