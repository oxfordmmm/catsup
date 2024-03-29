import csv
import os
import pathlib
import subprocess
import shlex
import time

import argh


def run(cmd, trace=True):
    if not os.environ.get("NO_TRACE") or not trace:
        print(cmd)
    if not os.environ.get("DUMMY_RUN"):
        attempt = 0
        while True:
            attempt += 1
            try:
                subprocess.check_output(shlex.split(cmd))
                break
            except Exception as e:
                if attempt > 12:
                    return {
                        "error_command": cmd,
                        "error_exception_str": str(e),
                    }
                else:
                    print(f"Error in upload. Attempt {attempt}. Sleeping for {2 ** attempt} seconds")
                    time.sleep(2 ** attempt)


def upload_file(par_url, u_file, cloud_prefix):
    u_file = pathlib.Path(u_file)
    cmd  = f"curl -f -X PUT -T {u_file} {par_url}{cloud_prefix}/{u_file.name}"
    error = run(cmd)
    return error


def mark_finished(par_url, u_dir, cloud_prefix):
    u_file = pathlib.Path(u_dir) / "upload_done.txt"
    u_file.touch()
    cmd = f"curl -f -X PUT --data-binary '@{u_file}' {par_url}{cloud_prefix}/{u_file.name}"
    error = run(cmd)
    return error


def upload_dir(par_url, u_dir, cloud_prefix):
    for u_file in pathlib.Path(u_dir).glob("*"):
        error = upload_file(par_url, u_file, cloud_prefix)
        if error:
            return error
    return mark_finished(par_url, u_dir, cloud_prefix)


def get_submission_name_from_sp3data_csv(u_dir):
    with open(u_dir / "sp3data.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            assert "submission_uuid4" in row
            submission_uuid4 = row["submission_uuid4"]
            return submission_uuid4


def upload_run(par_url, u_dir):
    u_dir = pathlib.Path(u_dir) / "upload"
    submission_uuid4 = get_submission_name_from_sp3data_csv(u_dir)
    error = upload_dir(par_url, u_dir, submission_uuid4)
    return error


if __name__ == "__main__":
    argh.dispatch_commands([upload_file, upload_dir, upload_run])
