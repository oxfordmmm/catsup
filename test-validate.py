import unittest
import validate

class TestValidate(unittest.TestCase):
    def test_validate_date_correctformat(self):
        input_data = ['2020-01-01',
                 '',
                 '01/01/2010',
                 '2010',
                 '2010-01',
                 '01-01']
        expected_results = [True,
                     False,
                     False,
                     False,
                     False,
                     False]

        for data, expected in zip(input_data, expected_results):
            result = validate.validate_date(data)
            print(f"validate_date ({data}) == {expected}?")
            self.assertEqual(expected, result)
    
    def test_validate_email(self):
        input_data = ['test@abc.com',
                 'test',
                 '@',
                 'abc.com',
                 'a.b@com',
                 '']
        expected_results = [True,
                     False,
                     False,
                     False,
                     False,
                     False]

        for data, expected in zip(input_data, expected_results):
            result = validate.validate_email(data)
            print(f"validate_email ({data}) == {expected}?")
            self.assertEqual(expected, result)

    def test_validate_template_correctrow(self):
        input_data = [{'index':1,
                      'subindex': 1,
                      'sample_name': 'P0001',
                      'sample_filename':'/data/qc_test/HG00114.downsampled.1.fastq.gz',
                      'sample_file_extension':'fastq.gz',
                      'sample_host':'human',
                      'sample_collection_date':'2020-01-01',
                      'sample_country':'United Kingdom',
                      'submission_title':'test',
                      'submission_description':'test submission',
                      'submitter_organisation':'test organisation',
                      'submitter_email':'test@test.com',
                      'instrument_platform':'Illumina pair-ended sequencing',
                      'instrument_model':'Illumina HiSeq 4000',
                      'instrument_flowcell':'96'}]
        expected_results = True

        result = validate.validate_template(input_data)
        self.assertEqual(expected_results, result)

    def test_validate_template_incorrectdate(self):
        input_data = [{'index':1,
                      'subindex': 1,
                      'sample_name': 'P0001',
                      'sample_filename':'/data/qc_test/HG00114.downsampled.1.fastq.gz',
                      'sample_file_extension':'fastq.gz',
                      'sample_host':'human',
                      'sample_collection_date':'20200101',
                      'sample_country':'United Kingdom',
                      'submission_title':'test',
                      'submission_description':'test submission',
                      'submitter_organisation':'test organisation',
                      'submitter_email':'test@test.com',
                      'instrument_platform':'Illumina pair-ended sequencing',
                      'instrument_model':'Illumina HiSeq 4000',
                      'instrument_flowcell':'96'}]
        expected_results = False

        result = validate.validate_template(input_data)
        self.assertEqual(expected_results, result)

    def test_validate_template_filepathnotexist(self):
        input_data = [{'index':1,
                      'subindex': 1,
                      'sample_name': 'P0001',
                      'sample_filename':'/qc_test/HG00114.downsampled.1.fastq.gz',
                      'sample_file_extension':'fastq.gz',
                      'sample_host':'human',
                      'sample_collection_date':'2020-01-01',
                      'sample_country':'United Kingdom',
                      'submission_title':'test',
                      'submission_description':'test submission',
                      'submitter_organisation':'test organisation',
                      'submitter_email':'test@test.com',
                      'instrument_platform':'Illumina pair-ended sequencing',
                      'instrument_model':'Illumina HiSeq 4000',
                      'instrument_flowcell':'96'}]
        expected_results = False

        result = validate.validate_template(input_data)
        self.assertEqual(expected_results, result)
    
    def test_validate_template_emptyfields(self):
        input_data = [{'index':'',
                      'subindex': '',
                      'sample_name': '',
                      'sample_filename':'/qc_test/HG00114.downsampled.1.fastq.gz',
                      'sample_file_extension':'fastq.gz',
                      'sample_host':'human',
                      'sample_collection_date':'2020-01-01',
                      'sample_country':'United Kingdom',
                      'submission_title':'test',
                      'submission_description':'test submission',
                      'submitter_organisation':'test organisation',
                      'submitter_email':'test@test.com',
                      'instrument_platform':'Illumina pair-ended sequencing',
                      'instrument_model':'Illumina HiSeq 4000',
                      'instrument_flowcell':'96'}]
        expected_results = False

        result = validate.validate_template(input_data)
        self.assertEqual(expected_results, result)
    
    def test_validate_template_invalidemail(self):
        input_data = [{'index':1,
                      'subindex': 1,
                      'sample_name': 'P0001',
                      'sample_filename':'/data/qc_test/HG00114.downsampled.1.fastq.gz',
                      'sample_file_extension':'fastq.gz',
                      'sample_host':'human',
                      'sample_collection_date':'2020-01-01',
                      'sample_country':'United Kingdom',
                      'submission_title':'test',
                      'submission_description':'test submission',
                      'submitter_organisation':'test organisation',
                      'submitter_email':'something',
                      'instrument_platform':'Illumina pair-ended sequencing',
                      'instrument_model':'Illumina HiSeq 4000',
                      'instrument_flowcell':'96'}]
        expected_results = False

        result = validate.validate_template(input_data)
        self.assertEqual(expected_results, result)


if __name__ == "__main__":
    unittest.main()
