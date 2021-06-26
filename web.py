"""This module provides a web interface to catsup"""

import collections
import csv
import threading
import json
import pathlib

import argh
import flask

import catsup

APP = flask.Flask("catsup-web")


def read_input_csv(submission_name):
    with open(pathlib.Path(submission_name) / "inputs.csv") as f:
        return list(csv.DictReader(f))


@APP.route("/", methods=["GET", "POST"])
def page1():
    debug_text = flask.request.form
    error_msg = None
    if debug_text:
        debug_text = json.dumps(debug_text, indent=4)

    if flask.request.method == "POST":
        submission_name = flask.request.form.get("submission_name")
        submission_dir = flask.request.form.get("submission_dir")

        r = catsup.create_template(submission_name, [submission_dir], api=True)

        if r["status"] == "error":
            error_msgs = {
                "input_csv_exists": f'This submission name "{submission_name}" already exists. Please pick another name.',
                "files_dir_missing": f'The submission directory "{submission_dir}" couldn\'t be accessed. Please check if it is correct and try again.',
            }
            error_msg = error_msgs.get(r.get("reason"), "Unknown error")

            return flask.render_template(
                "index.jinja2", debug_text=debug_text, error_msg=error_msg
            )

        if r["status"] == "success":
            return flask.redirect(f"/metadata/{submission_name}")

    return flask.render_template(
        "index.jinja2", debug_text=debug_text, error_msg=error_msg
    )


@APP.route("/metadata/<submission_name>", methods=["GET", "POST"])
def page2(submission_name):
    csvdata = read_input_csv(submission_name)

    debug_text = ""
    overrides = dict()
    truncate_sample_name = 0

    if flask.request.method == "POST":
        debug_text = flask.request.form
        overrides = flask.request.form
        truncate_sample_name = flask.request.form.get("truncate_sample_name", 0)

        if flask.request.form.get("submit_btn") == "Next step":
            # parse the form
            rows = collections.defaultdict(dict)
            for k, v in flask.request.form.items():
                if k[0:2] == "XX":
                    _, sample_index, sample_subindex, item_name = k.split("-")
                    rows[f"{sample_index}_{sample_subindex}"][item_name] = v
            # move inputs.csv to .inputs.csv.old
            (pathlib.Path(submission_name) / "inputs.csv").rename(".inputs.csv.old")
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
        submission_name=submission_name,
        csv=csvdata,
        debug_text=debug_text,
        overrides=overrides,
        truncate_sample_name=truncate_sample_name,
    )


@APP.route("/stage/<submission_name>", methods=["GET", "POST"])
def page3(submission_name):
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
        submission_name=submission_name,
        running=running,
        ok=ok,
        error=error,
        refresh=refresh,
    )


@APP.route("/upload/<submission_name>", methods=["GET", "POST"])
def page5(submission_name):
    running = False
    ok = False
    error = False
    refresh = False
    start = False
    if (pathlib.Path(submission_name) / ".step4-running").exists():
        running = True
    if (pathlib.Path(submission_name) / ".step4-ok").exists():
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
        submission_name=submission_name,
        running=running,
        fetch_uuid="cf5dcb73-f517-47ac-aed7-42d72aab976f",
        ok=ok,
        error=error,
        refresh=refresh,
    )


@APP.route("/pipeline/<submission_name>", methods=["GET", "POST"])
def page4(submission_name):
    running = False
    ok = False
    error = False
    refresh = False
    start = False
    if (pathlib.Path(submission_name) / ".step3-running").exists():
        running = True
    if (pathlib.Path(submission_name) / ".step3-ok").exists():
        ok = True
    if (pathlib.Path(submission_name) / ".step3-error").exists():
        error = True
    if flask.request.args.get("refresh") and not (ok or error):
        refresh = True
    if flask.request.args.get("start"):
        start = True

    if start:
        threading.Thread(target=catsup.run_pipeline, args=(submission_name,)).start()
        return flask.redirect(f"/pipeline/{submission_name}?refresh=1")

    return flask.render_template(
        "pipeline.jinja2",
        submission_name=submission_name,
        running=running,
        ok=ok,
        error=error,
        refresh=refresh,
    )


def main():
    APP.run(host="0.0.0.0", port=8080, debug=True)


if __name__ == "__main__":
    argh.dispatch_command(main)
