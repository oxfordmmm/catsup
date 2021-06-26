import pathlib, logging, sys, json

from dialog import Dialog
import argh


def change_out_key(submission_path, key, value):
    submission_path = pathlib.Path(submission_path)
    # some basic checks
    if not submission_path.is_dir():
        logging.error("{submission_path} is not a directory")
        sys.exit(1)
    if not (submission_path / "upload").is_dir():
        logging.error("{submission_path}/upload is not a directory")
        sys.exit(1)
    if not (submission_path / "upload" / "sp3data.csv").is_file():
        logging.error("{submission_path}/upload/sp3data.csv is not a file")
        sys.exit(1)
    # change key
    if (submission_path / "upload" / "upload.json").is_file():
        with open(submission_path / "upload" / "upload.json") as f:
            try:
                data = json.loads(f.read())
            except:
                data = dict()
    else:
        data = dict()
    data[key] = value
    with open(submission_path / "upload" / "upload.json", "w") as f:
        f.write(json.dumps(data, indent=4))


class Question:
    def __init__(self, qtype, qstr, key):
        self.qtype, self.qstr, self.key = qtype, qstr, key

    def execute(self, d, submission_name):
        if self.qtype == "yn":
            if d.yesno(self.qstr) == d.OK:
                change_out_key(submission_name, self.key, True)
            else:
                change_out_key(submission_name, self.key, False)


def gui(submission_name):
    d = Dialog(dialog="dialog")

    questions = [
        Question("yn", "can we use your data for good?", "data-use-good"),
        Question("yn", "can we use your data for food?", "data-use-grey"),
        Question("yn", "can we use your data for evil?", "data-use-evil"),
    ]

    for q in questions:
        q.execute(d, submission_name)

    d.msgbox("Thanks!")


if __name__ == "__main__":
    argh.dispatch_commands([change_out_key, gui])
