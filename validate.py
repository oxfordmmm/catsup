#! /usr/bin/env python3

import csv, logging, pathlib, json
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

def validate_template(reader):
    failed = False
    for row in reader:
        for k, v in row.items():
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
                failed = True
    return not failed

def validate_config(config):
    if type(config) != dict:
        logging.error("Failed to validate config:")
        logging.error("Config is not a dictionary")
        return False

    must_have_keys = ['number_of_example_samples', 'pipeline', 'pipelines', 'nextflow_additional_params']

    for must_have_key in must_have_keys:
        if must_have_key not in config:
            logging.error("Failed to validate config:")
            logging.error(f"Key '{must_have_key}' missing from config")
            return False

    pipeline = config['pipeline']
    pipelines = config["pipelines"]

    if type(pipeline) != str:
        logging.error("Failed to validate config:")
        logging.error("Key pipeline is not a string")
        return False
    
    if type(pipelines) != dict:
        logging.error("Failed to validate config:")
        logging.error("Key pipelines is not a dict")
        return False

    if pipeline not in pipelines:
        logging.error("Failed to validate config:")
        logging.error(f"Pipeline {pipeline} has no configuration")
        return False

    pipeline_must_have_keys = ['script', 'image', 'human_ref']
    
    for pipeline_name, pipeline_conf in pipelines.items():
        if type(pipeline_conf) != dict:
            logging.error("Failed to validate config:")
            logging.error(f"{pipeline_name} value is not a dict")
            return False

        for pipeline_must_have_key in pipeline_must_have_keys:
            if pipeline_must_have_key not in pipeline_conf:
                logging.error("Failed to validate config:")
                logging.error(f"{pipeline_name} config is missing key {pipeline_must_have_key}")
                return False

        for k, v in pipeline_conf.items():
            if not pathlib.Path(v).exists():
                logging.error("Failed to validate config:")
                logging.error(f"Pipeline config {pipeline_name}: file {v} does not exist")
                return False

    if 'upload' in config:
        if 's3' in config['upload']:
            s3_must_have_keys = ['bucket', 's3cmd-config']
            for upload_must_have_key in s3_must_have_keys:
                if upload_must_have_key not in config['upload']['s3']:
                    logging.error("Failed to validate config:")
                    logging.error(f"S3 config s3: key {upload_must_have_key} does not exist")
                    return False
            cfg_file = config['upload']['s3']['s3cmd-config']
            if not validate_filepath(cfg_file):
                logging.error("Failed to validate config:")
                logging.error(f"S3 config file: file {cfg_file} does not exist")
                return False   
    
    return True
