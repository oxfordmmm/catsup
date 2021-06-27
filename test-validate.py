# Test test-validate.py
# Run all tests: python3 test-validate.py
# Run one test:  python3 test-validate.py TestValidate.test_validate_date_correctformat
# Run code coverage: coverge run test-validate.py
# View code coverage report: coverage report -m
# Generate code coverage html report: coverage html

import json
import os
import unittest

import validate


class TestValidate(unittest.TestCase):
    def setUp(self):
        os.system("mkdir /tmp/catsup")
        os.system("touch /tmp/catsup/test1.fastq.gz")
        os.system("touch /tmp/catsup/catsup-kraken2.nf")
        os.system("touch /tmp/catsup/fatos.img")
        os.system("touch /tmp/catsup/human_ref")
        os.system("touch /tmp/catsup/.s3cfg-catsup")

    @classmethod
    def tearDownClass(cls):
        os.system("rm -rf /tmp/catsup")

    def test_validate_date_correctformat(self):
        input_data = ["2020-01-01", "", "01/01/2010", "2010", "2010-01", "01-01"]
        expected_results = [True, False, False, False, False, False]

        for data, expected in zip(input_data, expected_results):
            result = validate.validate_date(data)
            print(f"validate_date ({data}) == {expected}?")
            self.assertEqual(expected, result)

    def test_validate_email(self):
        input_data = ["test@abc.com", "test", "@", "abc.com", "a.b@com", ""]
        expected_results = [True, False, False, False, False, False]

        for data, expected in zip(input_data, expected_results):
            result = validate.validate_email(data)
            print(f"validate_email ({data}) == {expected}?")
            self.assertEqual(expected, result)

    def test_validate_template_correctrow(self):
        input_data = [
            {
                "index": 1,
                "subindex": 1,
                "sample_name": "P0001",
                "sample_filename": "/tmp/catsup/test1.fastq.gz",
                "sample_file_extension": "fastq.gz",
                "sample_host": "human",
                "sample_collection_date": "2020-01-01",
                "sample_country": "United Kingdom",
                "submission_title": "test",
                "submission_description": "test submission",
                "submitter_organisation": "test organisation",
                "submitter_email": "test@test.com",
                "instrument_platform": "Illumina pair-ended sequencing",
                "instrument_model": "Illumina HiSeq 4000",
                "instrument_flowcell": "96",
            }
        ]
        expected_results = True

        result = validate.validate_template(input_data)
        self.assertEqual(expected_results, result)

    def test_validate_template_incorrectdate(self):
        input_data = [
            {
                "index": 1,
                "subindex": 1,
                "sample_name": "P0001",
                "sample_filename": "/tmp/catsup/test1.fastq.gz",
                "sample_file_extension": "fastq.gz",
                "sample_host": "human",
                "sample_collection_date": "20200101",
                "sample_country": "United Kingdom",
                "submission_title": "test",
                "submission_description": "test submission",
                "submitter_organisation": "test organisation",
                "submitter_email": "test@test.com",
                "instrument_platform": "Illumina pair-ended sequencing",
                "instrument_model": "Illumina HiSeq 4000",
                "instrument_flowcell": "96",
            }
        ]
        expected_results = False

        result = validate.validate_template(input_data)
        self.assertEqual(expected_results, result)

    def test_validate_template_filepath_notexist(self):
        input_data = [
            {
                "index": 1,
                "subindex": 1,
                "sample_name": "P0001",
                "sample_filename": "/tmp/catsup/nofile.fastq.gz",
                "sample_file_extension": "fastq.gz",
                "sample_host": "human",
                "sample_collection_date": "2020-01-01",
                "sample_country": "United Kingdom",
                "submission_title": "test",
                "submission_description": "test submission",
                "submitter_organisation": "test organisation",
                "submitter_email": "test@test.com",
                "instrument_platform": "Illumina pair-ended sequencing",
                "instrument_model": "Illumina HiSeq 4000",
                "instrument_flowcell": "96",
            }
        ]
        expected_results = False

        result = validate.validate_template(input_data)
        self.assertEqual(expected_results, result)

    def test_validate_template_emptyfields(self):
        input_data = [
            {
                "index": "",
                "subindex": "",
                "sample_name": "",
                "sample_filename": "/tmp/catsup/test1.fastq.gz",
                "sample_file_extension": "fastq.gz",
                "sample_host": "human",
                "sample_collection_date": "2020-01-01",
                "sample_country": "United Kingdom",
                "submission_title": "test",
                "submission_description": "test submission",
                "submitter_organisation": "test organisation",
                "submitter_email": "test@test.com",
                "instrument_platform": "Illumina pair-ended sequencing",
                "instrument_model": "Illumina HiSeq 4000",
                "instrument_flowcell": "96",
            }
        ]
        expected_results = False

        result = validate.validate_template(input_data)
        self.assertEqual(expected_results, result)

    def test_validate_template_invalidemail(self):
        input_data = [
            {
                "index": 1,
                "subindex": 1,
                "sample_name": "P0001",
                "sample_filename": "/tmp/catsup/test1.fastq.gz",
                "sample_file_extension": "fastq.gz",
                "sample_host": "human",
                "sample_collection_date": "2020-01-01",
                "sample_country": "United Kingdom",
                "submission_title": "test",
                "submission_description": "test submission",
                "submitter_organisation": "test organisation",
                "submitter_email": "something",
                "instrument_platform": "Illumina pair-ended sequencing",
                "instrument_model": "Illumina HiSeq 4000",
                "instrument_flowcell": "96",
            }
        ]
        expected_results = False

        result = validate.validate_template(input_data)
        self.assertEqual(expected_results, result)

    def test_validate_config_noconfig(self):
        input_data = "{}"
        expected_results = False

        result = validate.validate_config(input_data)
        self.assertEqual(expected_results, result)

    def test_validate_config_nopipelineimage(self):
        input_data = """
             {"number_of_example_samples": 1,
                "pipeline": "catsup-kraken2",
                "pipelines": {
                "catsup-kraken2":
                {
                    "script": "/tmp/catsup/catsup-kraken2.nf",
                    "image": "/tmp/catsup/nofatos.img",
                    "human_ref": "/tmp/catsup/human_ref"
                }},
                "upload":
                {
                "s3":
                {
                    "bucket": "s3://mmm-sp3-alpha",
                    "s3cmd-config": "/tmp/catsup/.s3cfg-catsup"
                }}}
            """

        input_dict = json.loads(input_data)
        expected_results = False
        result = validate.validate_config(input_dict)
        self.assertEqual(expected_results, result)

    def test_validate_config_nopipelinescript(self):
        input_data = """
             {"number_of_example_samples": 1,
                "pipeline": "catsup-kraken2",
                "pipelines": {
                "catsup-kraken2":
                {
                     "script": "/tmp/nocatsup.nf",
                    "image": "/tmp/catsup/fatos.img",
                    "human_ref": "/tmp/catsup/human_ref"
                }},
                "upload":
                {
                "s3":
                {
                    "bucket": "s3://mmm-sp3-alpha",
                    "s3cmd-config": "/tmp/catsup/.s3cfg-catsup"
                }}}
            """

        input_dict = json.loads(input_data)
        expected_results = False
        result = validate.validate_config(input_dict)
        self.assertEqual(expected_results, result)

    def test_validate_config_nopipelines(self):
        input_data = """
            {"number_of_example_samples": 1,
            "pipeline": "catsup-kraken2",
            "upload":
            {
            "s3":
            {
                "bucket": "s3://mmm-sp3-alpha",
                "s3cmd-config": "/tmp/catsup/.s3cfg-catsup"
            }}}
            """

        input_dict = json.loads(input_data)
        expected_results = False
        result = validate.validate_config(input_dict)
        self.assertEqual(expected_results, result)

    def test_validate_config_fullconfig(self):
        input_data = """
                {"number_of_example_samples": 1,
                "pipeline": "catsup-kraken2",
                "pipelines": {
                "catsup-kraken2":
                {
                    "script": "/tmp/catsup/catsup-kraken2.nf",
                    "image": "/tmp/catsup/fatos.img",
                    "human_ref": "/tmp/catsup/human_ref"
                }},
                "upload":
                {
                "s3":
                {
                    "bucket": "s3://mmm-sp3-alpha",
                    "s3cmd-config": "/tmp/catsup/.s3cfg-catsup"
                }}}
                """

        input_dict = json.loads(input_data)
        expected_results = True
        result = validate.validate_config(input_dict)
        self.assertEqual(expected_results, result)


if __name__ == "__main__":
    unittest.main()
