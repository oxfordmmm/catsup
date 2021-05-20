import os
import pathlib
import csv
import argh

def run(cmd, trace=True):
    if not os.environ.get("NO_TRACE") or not trace:
        print(cmd)
    if not os.environ.get("DUMMY_RUN"):
        os.system(cmd)

def upload_file(par_url, u_file, cloud_prefix):
    u_file = pathlib.Path(u_file)
    cmd = f"curl -X PUT --data-binary '@{u_file}' {par_url}{cloud_prefix}/{u_file.name}"
    run(cmd)

def upload_dir(par_url, u_dir, cloud_prefix):
    for u_file in pathlib.Path(u_dir).glob("*"):
        upload_file(par_url, u_file, cloud_prefix)

def get_submission_name_from_sp3data_csv(u_dir):
    with open(u_dir / 'sp3data.csv') as f:
        reader = csv.DictReader(f)
        for row in reader:
            assert('submission_uuid4' in row)
            submission_uuid4 = row['submission_uuid4']
            return submission_uuid4

def upload_run(par_url, u_dir):
    u_dir = pathlib.Path(u_dir) / 'upload'
    submission_uuid4 = get_submission_name_from_sp3data_csv(u_dir)
    upload_dir(par_url, u_dir, submission_uuid4)

if __name__ == "__main__":
    argh.dispatch_commands([upload_file, upload_dir, upload_run])
