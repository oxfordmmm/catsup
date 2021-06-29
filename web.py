"""This module provides a web interface to catsup"""

import collections
import csv
import json
import os
import pathlib
import shutil
import threading
import time
import webbrowser

import argh
import flask
import psutil

import catsup

APP = flask.Flask("catsup-web")


def read_input_csv(submission_name):
    with open(pathlib.Path(submission_name) / "inputs.csv") as f:
        return list(csv.DictReader(f))


def get_submission_uuid4(submission_name):
    try:
        with open(pathlib.Path(submission_name) / "upload" / "sp3data.csv") as f:
            return list(csv.DictReader(f))[0]["submission_uuid4"]
    except Exception as e:
        print(str(e))


def get_submissions():
    ps = pathlib.Path(".").glob("*/inputs.csv")
    files = sorted(list(ps), key=os.path.getmtime, reverse=True)
    return [x.parent.name for x in files]


def get_submission_files(submission_name):
    files = (pathlib.Path(submission_name) / "pipeline_in").glob("*")
    files = sorted([x.name for x in files])
    return files


def get_submission_sample_map(submission_name):
    try:
        with open(pathlib.Path(submission_name) / "sample_uuid_map.csv") as f:
            return sorted(list(csv.DictReader(f)), key=lambda x: x["sample_uuid4"])
    except Exception as e:
        print(str(e))
        return list()


def get_nextflow_log(submission_name):
    try:
        with open(
            pathlib.Path(submission_name) / "pipeline_run" / ".nextflow.log"
        ) as f:
            return f.read()
    except:
        return None


def k(key, d, sep="."):
    try:
        for kp in key.split(sep):
            d = d[kp]
        return d
    except:
        return None


def config_error_check():
    errors = list()
    try:
        with open("config.json") as f:
            conf_data = f.read()
    except Exception as e:
        errors.append({"code": "config_json_read_error", "details": str(e)})
        return errors  # no further error handling possible
    try:
        conf = json.loads(conf_data)
    except Exception as e:
        errors.append({"code": "config_json_json_error", "details": str(e)})
        return errors  # no further error handling possible

    for key in [
        "pipeline",
        "container",
        "nextflow_additional_params",
        "pipelines",
        "pipelines.catsup-kraken2",
        "pipelines.catsup-kraken2.script",
        "pipelines.catsup-kraken2.image",
        "pipelines.catsup-kraken2.human_ref",
    ]:
        if not k(key, conf):
            errors.append({"code": "config_json_missing_key", "details": key})

    for f in [
        "pipelines.catsup-kraken2.script",
        "pipelines.catsup-kraken2.image",
        "pipelines.catsup-kraken2.human_ref",
    ]:
        f = k(f, conf)
        if f:
            if not pathlib.Path(f).exists():
                errors.append({"code": "config_json_missing_file", "details": f})

    for exe in [
        "nextflow",
        "curl",
        "md5sum",
        "sha1sum",
        "sha512sum",
        "s3cmd",
        "kraken2",
        "trim_galore",
        "seqtk",
    ]:
        if not shutil.which(exe):
            errors.append({"code": "missing_executable", "details": exe})

    mem_total = psutil.virtual_memory().total // 1000000000
    mem_req = 16
    if mem_total < mem_req:
        errors.append(
            {
                "code": "low_memory",
                "details": f"Less than {mem_req}GB RAM total. Standard preprocessing pipeline won't work well.",
            }
        )

    return errors


@APP.route("/")
def index():
    subs = get_submissions()
    errors = config_error_check()
    return flask.render_template(
        "index.jinja2", title="SP3 Upload Client", subs=subs, errors=errors
    )


@APP.route("/submission_details/<submission_name>", methods=["GET", "POST"])
def submission_details(submission_name):
    submission_uuid4 = get_submission_uuid4(submission_name)
    submission_files = get_submission_files(submission_name)
    submission_sample_map_ = get_submission_sample_map(submission_name)
    submission_sample_map = list()
    nf_log = get_nextflow_log(submission_name)
    memo = list()
    for s in submission_sample_map_:
        if s["sample_name"] not in memo:
            memo.append(s["sample_name"])
            submission_sample_map.append(s)

    buttons = dict()
    if pathlib.Path(submission_name).is_dir():
        buttons["delete_submission_dir"] = True
    if (pathlib.Path(submission_name) / "upload").is_dir():
        buttons["delete_upload_dir"] = True

    if flask.request.method == "POST":
        if "delete_submission_dir" in flask.request.form:

            def delete_submission_dir():
                shutil.rmtree(pathlib.Path(submission_name))

            threading.Thread(target=delete_submission_dir).start()
            time.sleep(2)  # optimism
            return flask.redirect("/")
        if "delete_upload_dir" in flask.request.form:

            def delete_upload_dir():
                shutil.rmtree(pathlib.Path(submission_name) / "upload")

            threading.Thread(target=delete_work_dir).start()
            buttons["delete_upload_dir"] = False

    return flask.render_template(
        "submission_details.jinja2",
        title="Submission Details",
        submission_name=submission_name,
        submission_uuid4=submission_uuid4,
        submission_files=submission_files,
        submission_sample_map=submission_sample_map,
        nf_log=nf_log,
        buttons=buttons,
    )


@APP.route("/new_submission", methods=["GET", "POST"])
def page1():
    title = "Start New Submission"

    def save_par_url(submission_name, par_url):
        try:
            with open(pathlib.Path(submission_name) / ".par_url", "w") as f:
                f.write(par_url)
        except Exception as e:
            return str(e)

    error_msg = None
    if flask.request.method == "POST":
        submission_name = flask.request.form.get("submission_name")
        submission_dir = flask.request.form.get("submission_dir")
        submission_par_url = flask.request.form.get("submission_par_url")
        submission_files_per_sample = flask.request.form.get(
            "submission_files_per_sample"
        )
        try:
            submission_files_per_sample = int(submission_files_per_sample)
        except:
            error_msg = "Couldn't parse files per sample as a number"
            return flask.render_template(
                "new_submission.jinja2", title=title, error_msg=error_msg
            )
        if not submission_name:
            error_msg = "Submission name can't be empty"
            return flask.render_template(
                "new_submission.jinja2", title=title, error_msg=error_msg
            )
        if not submission_dir:
            error_msg = "Submission directory can't be empty"
            return flask.render_template(
                "new_submission.jinja2", title=title, error_msg=error_msg
            )

        r = catsup.create_template(
            submission_name, [submission_dir], submission_files_per_sample, api=True
        )
        try:
            with open(pathlib.Path(submission_name) / ".files_per_sample", "w") as f:
                f.write(str(submission_files_per_sample))
        except:
            error_msg = "Couldn't save number of files sample to .files_per_sample"
            return flask.render_template(
                "new_submission.jinja2", title=title, error_msg=error_msg
            )

        r2 = save_par_url(submission_name, submission_par_url)

        if r["status"] == "error":
            error_msgs = {
                "input_csv_exists": f'This submission name "{submission_name}" already exists. Please pick another name.',
                "files_dir_missing": f'The submission directory "{submission_dir}" couldn\'t be accessed. Please check if it is correct and try again.',
            }
            error_msg = error_msgs.get(r.get("reason"), "Unknown error")

            return flask.render_template(
                "new_submission.jinja2", title=title, error_msg=error_msg
            )

        if r2:
            error_msg = "Couldn't save par_url"
            return flask.render_template(
                "new_submission.jinja2", title=title, error_msg=error_msg
            )

        if r["status"] == "success":
            return flask.redirect(f"/metadata/{submission_name}")

    return flask.render_template(
        "new_submission.jinja2", title=title, error_msg=error_msg
    )


def find_sample_name_mismatch(rows):
    """
    if we have eg. paired sample file names file1_1.fastq.gz and file1_2.fastq.gz
    then both of these files must have the same sample name (probably file1)

    This function returns any mismatches
    """
    ret = list()
    for (index, subindex), row in rows.items():
        if subindex != 1:
            sam_name_1 = row.get("sample_name")
            sam_name_2 = rows.get((index, "1"), dict()).get("sample_name")
            if sam_name_1 != sam_name_2:
                ret.append((index, sam_name_1, sam_name_2))
    return ret


@APP.route("/metadata/<submission_name>", methods=["GET", "POST"])
def page2(submission_name):
    csvdata = read_input_csv(submission_name)

    overrides = dict()
    truncate_sample_name = 0

    if flask.request.method == "POST":
        overrides = flask.request.form
        truncate_sample_name = flask.request.form.get("truncate_sample_name", 0)

        if flask.request.form.get("submit_btn") == "Next step":
            # parse the form
            rows = collections.defaultdict(dict)
            for k, v in flask.request.form.items():
                if k[0:2] == "XX":
                    _, sample_index, sample_subindex, item_name = k.split("-")
                    rows[(sample_index, sample_subindex)][item_name] = v

            # backup inputs.csv to .inputs.csv.old
            # TODO doesn't work?
            # (pathlib.Path(submission_name) / "inputs.csv").rename(".inputs.csv.old")

            # find samples that have mismatched names
            ret = find_sample_name_mismatch(rows)
            if ret:
                errors = list()
                for r in ret:
                    errors.append(
                        f"Sample files for sample #{r[0]} have different sample names: {r[1]} and {r[2]}."
                    )

                return flask.render_template(
                    "metadata.jinja2",
                    title="Step 1: Edit Submission Metadata",
                    submission_name=submission_name,
                    csv=csvdata,
                    overrides=overrides,
                    truncate_sample_name=truncate_sample_name,
                    errors=errors,
                )

            # save new inputs.csv
            with open(
                pathlib.Path(submission_name) / "inputs.csv", "w", newline=""
            ) as csvfile:
                writer = csv.DictWriter(
                    csvfile,
                    fieldnames=[
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
                    ],
                )
                writer.writeheader()
                for _, row in rows.items():
                    print(row)
                    writer.writerow(row)

            return flask.redirect(f"/stage/{submission_name}")

    return flask.render_template(
        "metadata.jinja2",
        title="Step 1: Edit Submission Metadata",
        submission_name=submission_name,
        csv=csvdata,
        overrides=overrides,
        truncate_sample_name=truncate_sample_name,
    )


@APP.route("/stage/<submission_name>", methods=["GET", "POST"])
def page3(submission_name):
    title = "Step 2: Prepare data for pipeline"
    running = False
    ok = False
    error = False
    refresh = False
    start = False
    if (pathlib.Path(submission_name) / ".step2-running").exists():
        running = True
    if (pathlib.Path(submission_name) / ".step2-ok").exists():
        ok = True
    if (pathlib.Path(submission_name) / ".step2-error").exists():
        error = True
    if flask.request.args.get("refresh") and not (ok or error):
        refresh = True
    if flask.request.args.get("start"):
        start = True

    if start:
        threading.Thread(target=catsup.prepare_data, args=(submission_name,)).start()
        return flask.redirect(f"/stage/{submission_name}?refresh=1")

    return flask.render_template(
        "stage.jinja2",
        title=title,
        submission_name=submission_name,
        running=running,
        ok=ok,
        error=error,
        refresh=refresh,
    )


@APP.route("/pipeline/<submission_name>", methods=["GET", "POST"])
def page4(submission_name):
    title = "Step 3: Run preprocessing pipeline"
    running = False
    ok = False
    error = ""
    refresh = False
    start = False
    nf_log = None
    if (pathlib.Path(submission_name) / ".step3-running").exists():
        running = True
    if (pathlib.Path(submission_name) / ".step3-ok").exists():
        ok = True
    if (pathlib.Path(submission_name) / ".step3-error").exists():
        error = "Nextflow failed"
    if flask.request.args.get("refresh") and not (ok or error):
        refresh = True
    if flask.request.args.get("start"):
        start = True
    if running or ok or error:
        nf_log = get_nextflow_log(submission_name)

    try:
        with open(pathlib.Path(submission_name) / ".files_per_sample") as f:
            number_of_files_per_sample = int(f.read())
    except:
        error = "Couldn't read .files_per_sample file"
        return flask.render_template(
            "pipeline.jinja2",
            title=title,
            submission_name=submission_name,
            running=running,
            ok=ok,
            error=error,
            refresh=refresh,
            nf_log=nf_log,
        )

    if start:
        threading.Thread(
            target=catsup.run_pipeline,
            args=(submission_name, number_of_files_per_sample),
        ).start()
        return flask.redirect(f"/pipeline/{submission_name}?refresh=1")

    return flask.render_template(
        "pipeline.jinja2",
        title=title,
        submission_name=submission_name,
        running=running,
        ok=ok,
        error=error,
        refresh=refresh,
        nf_log=nf_log,
    )


@APP.route("/upload/<submission_name>", methods=["GET", "POST"])
def page5(submission_name):
    title = "Step 4: Upload to cloud storage"
    running = False
    ok = False
    error = False
    refresh = False
    start = False
    submission_uuid4 = None
    if (pathlib.Path(submission_name) / ".step4-running").exists():
        running = True
    if (pathlib.Path(submission_name) / ".step4-ok").exists():
        submission_uuid4 = get_submission_uuid4(submission_name)
        ok = True
    if (pathlib.Path(submission_name) / ".step4-error").exists():
        error = True
    if flask.request.args.get("refresh") and not (ok or error):
        refresh = True
    if flask.request.args.get("start"):
        start = True

    if start:
        threading.Thread(target=catsup.upload_to_sp3, args=(submission_name,)).start()
        return flask.redirect(f"/upload/{submission_name}?refresh=1")

    return flask.render_template(
        "upload.jinja2",
        title=title,
        submission_name=submission_name,
        running=running,
        submission_uuid4=submission_uuid4,
        ok=ok,
        error=error,
        refresh=refresh,
    )


def main():
    if os.environ.get("FLASK_DEBUG"):
        APP.run(host="127.0.0.1", port=8080, debug=True)
    else:

        def browser_open():
            time.sleep(5)  # optimism
            webbrowser.open_new("http://127.0.0.1:8080")

        threading.Thread(target=browser_open).start()
        APP.run(host="127.0.0.1", port=8080)


if __name__ == "__main__":
    argh.dispatch_command(main)
