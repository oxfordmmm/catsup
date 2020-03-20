import csv, logging, pathlib
import re

in_fieldnames_date_fields = ['sample_collection_date']
in_fieldnames_email_fields = ['submitter_email']
in_fieldnames_filepath_fields = ['sample_filename']

def validate_date(s):
    try:
        year = int(s[0:4])
        if year < 1900 or year > 2100:
            raise Exception
        month = int(s[5:7])
        if month < 1 or month > 12:
            raise Exception
        day = int(s[8:10])
        if day < 1 or day > 31:
            raise Exception
        return True
    except:
        return False

def validate_email(s):
    regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
    if(re.search(regex,s)):
        return True
    else:
        return False

def validate_filepath(s):
    return pathlib.Path(s).exists()

def validate_template(submission_name, in_csv_name, in_fieldnames):
    input_csv = pathlib.Path(submission_name) / in_csv_name

    if not pathlib.Path(input_csv).exists():
        logging.error(f'File {input_csv} doesn\'t exists. Can\'t validate.')
        sys.exit(1)

    with open(input_csv, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)

        if reader.fieldnames != in_fieldnames:
            logging.error(f"File {input_csv} has wrong header:")
            logging.error(f"Expected: {in_fieldnames}")
            logging.error(f"Received: {reader.fieldnames}")
            sys.exit(1)

        failed = False
        for row in reader:
            for k, v in row.items():
                if set(row.keys()) != set(in_fieldnames): # is this even possible?
                    logging.error(f"Row keys don't match model: {row}")
                    failed = True
                if not v:
                    logging.error(f"Found empty value in row: {row}")
                    logging.error(f"Column {k} is empty")
                    failed = True
                if k in in_fieldnames_date_fields and not validate_date(v):
                    logging.error(f"Found date in invalid format: {row}")
                    logging.error(f"Column {k} date is {v}")
                    logging.error("Expected date format YYYY-MM-DD")
                    failed = True
                if k in in_fieldnames_email_fields and not validate_email(v):
                    logging.error(f"Found email in invalid format: {row}")
                    logging.error(f"Column {k} email format is {v}")
                    failed = True
                if k in in_fieldnames_filepath_fields and not validate_filepath(v):
                    logging.error(f"File path {v} doesn't exist in {row}")
                    logging.error(f"Column {k} file path is {v}")
        if not failed:
            print(f"{input_csv} validated")
    return not failed
