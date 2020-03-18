# Catsup
Catsup is a python script for SP3 users to pre-processing local pathogen sequencing data and upload data to a data storage (S3 bucket) for SP3 to process.

## What does catsup do?

### Prepare the template
1. Generates a template for data submission
2. Validates the template after user input

### Anonymizing sample identifier
3. Creates unique identifier (UUID) for submission
4. Creates unique identifier (UUID) for every sample
5. Generate md5sum for each sample file
6. Update the template with submission UUID, sample guid and md5sum
7. Rename/symlink sample files with sample UUID
8. Generates a lookup table of sample name and sample guid

### Removing human reads
9. Run quality control pipeline (trimming and remove human reads)

### Upload to a S3 bucket
10. Upload cleaned (no human reads) sample files to S3 buckets

## User template example

| index | subindex | sample_name | sample_filename | sample_file_extension | sample_host | sample_collection_date | sample_country | submission_title | submission_description | submitter_organisation | submitter_email | instrument_platform | instrument_model | instrument_flowcell |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | 
1 | 1 | P0001 | in/P0001_1.fastq.gz | fastq.gz | Homo sapiens | 2020-01-30 | United Kingdom | Bacteria infection study | Bacteria infection study for drug resistance | University of Oxford | crookit@ndm.ox.ac.uk | Illumina pair-ended sequencing | Illumina HiSeq 4000 | 96
1 | 2 | P0001 | in/P0001_2.fastq.gz | fastq.gz | Homo sapiens | 2020-01-30 | United Kingdom | Bacteria infection study | Bacteria infection study for drug resistance | University of Oxford | crookit@ndm.ox.ac.uk | Illumina pair-ended sequencing | Illumina HiSeq 4000 | 96
2 | 1 | P0002 | in/P0002_1.fastq.gz | fastq.gz | Homo sapiens | 2020-01-30 | United Kingdom | Bacteria infection study | Bacteria infection study for drug resistance | University of Oxford | crookit@ndm.ox.ac.uk | Illumina pair-ended sequencing | Illumina HiSeq 4000 | 96
2 | 2 | P0002 | in/P0002_2.fastq.gz | fastq.gz | Homo sapiens | 2020-01-30 | United Kingdom | Bacteria infection study | Bacteria infection study for drug resistance | University of Oxford | crookit@ndm.ox.ac.uk | Illumina pair-ended sequencing | Illumina HiSeq 4000 | 96
3 | 1 | P0003 | in/P0003_1.fastq.gz | fastq.gz | Homo sapiens | 2020-01-30 | United Kingdom | Bacteria infection study | Bacteria infection study for drug resistance | University of Oxford | crookit@ndm.ox.ac.uk | Illumina pair-ended sequencing | Illumina HiSeq 4000 | 96
3 | 2 | P0003 | in/P0003_2.fastq.gz | fastq.gz | Homo sapiens | 2020-01-30 | United Kingdom | Bacteria infection study | Bacteria infection study for drug resistance | University of Oxford | crookit@ndm.ox.ac.uk | Illumina pair-ended sequencing | Illumina HiSeq 4000 | 96

## UUID and sample mapping table

Sample names and sample file names are renamed to UUIDs.

The map between sample names and UUIDs are written to a file named sample_uuid_map.csv, which is to be kept by the user to allow mapping processed samples back to sample names.

|sample_name|sample_uuid4|original_file|renamed_file|
| - | - | - | - |
|P0001 | 87e22c5e-3a02-4edb-ad9d-303a36d9f7ee | in/P0001_1.fastq.gz | 87e22c5e-3a02-4edb-ad9d-303a36d9f7ee_1.fastq.gz|
|P0001 | 87e22c5e-3a02-4edb-ad9d-303a36d9f7ee | in/P0001_2.fastq.gz | 87e22c5e-3a02-4edb-ad9d-303a36d9f7ee_2.fastq.gz|
|P0002 | 3310d206-c1e9-4b41-9efc-4c8da7eca3c4 | in/P0002_1.fastq.gz | 3310d206-c1e9-4b41-9efc-4c8da7eca3c4_1.fastq.gz|
|P0002 | 3310d206-c1e9-4b41-9efc-4c8da7eca3c4 | in/P0002_2.fastq.gz | 3310d206-c1e9-4b41-9efc-4c8da7eca3c4_2.fastq.gz|
|P0003 | fff6ead2-d1ec-470b-b0a1-8935dbbe3212 | in/P0003_1.fastq.gz | fff6ead2-d1ec-470b-b0a1-8935dbbe3212_1.fastq.gz|
|P0003 | fff6ead2-d1ec-470b-b0a1-8935dbbe3212 | in/P0003_2.fastq.gz | fff6ead2-d1ec-470b-b0a1-8935dbbe3212_2.fastq.gz|
