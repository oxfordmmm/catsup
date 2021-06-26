import csv
import json
import pathlib

import argh
import flask

import catsup

app = flask.Flask("catsup-web")


def read_input_csv(submission_name):
    with open(pathlib.Path(submission_name) / "inputs.csv") as f:
        return list(csv.DictReader(f))


@app.route("/", methods=["GET", "POST"])
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


@app.route("/metadata/<submission_name>", methods=["GET", "POST"])
def page2(submission_name):
    csv = read_input_csv(submission_name)

    debug_text = ""
    overrides = dict()
    truncate_sample_name = 0

    if flask.request.method == "POST":
        debug_text = flask.request.form
        overrides = flask.request.form
        truncate_sample_name = flask.request.form.get("truncate_sample_name", 0)

    return flask.render_template(
        "metadata.jinja2",
        submission_name=submission_name,
        csv=csv,
        debug_text=debug_text,
        overrides=overrides,
        truncate_sample_name=truncate_sample_name,
    )


def main():
    app.run(host="0.0.0.0", port=8080, debug=True)


if __name__ == "__main__":
    argh.dispatch_command(main)
