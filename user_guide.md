# Catsup - GPAS User Guide

2021-06-28 by Oliver Bannister

This user guide is designed to take you through, step-by-step, the process required to use Catsup to upload sequencing data to GPAS. It prepares meta-data, removes human reads and uploads sequencing fastq files to a dedicated storage like Oracle cloud which GPAS uses.

## WHAT IS CATSUP?

Catsup is a python application that allows users to pre-process pathogen sequencing data and upload it to the Genome Pathogen Analysis System (GPAS).

## WHAT DOES CATSUP DO?

Catsup performs the following steps:

Prepares the Template
    1. Generates a template for data submission (input.csv)
    2. Validates the template after user input

Anonymises Sample Identifiers
    3. Creates unique identifier (UUID) for submission
    4. Creates unique identifier (UUID) for every sample
    5. Generates md5sum for each sample file
    6. Updates the template with submission UUID, sample guid and md5sum (sp3data.csv)
    7. Rename/symlink sample files with sample UUID
    8. Generates a lookup table of sample name and sample guid (sample_uuid_map.csv)

Removes Human Reads
    9. Run quality control pipeline (trimming and remove human reads)

Upload to GPAS
    10. Upload cleaned (no human reads) sample files to GPAS

## REQUIREMENTS

### Software

We strongly recommend installing Catsup using conda (see later in guide). Ubuntu 18.04 is highly recommended as the base OS as that has been tested the most. Using Windows Subsystem for Linux is possible as a workaround if only Windows based systems are available.

### Skills

A knowledge of Linux-type work is helpful when using Catsup, however the following guide should make it accessible to new users.

### Hardware

Catsup and its pipelines require decent memory (10gb+RAM) to function successfully. We strongly recommend that you run it on a dedicated or virtual machine. Running it alongside other applications may cause it to fail.

It can be run on a cluster however.

A reliable and fast internet connection is also recommended due to the size of upload files required.

## Step-by-Step User Guide

### Install Miniconda3

Open your terminal and type:

    $ wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

to download the Minconda install script

    $ chmod +x Miniconda3-latest-Linux-x86_64.sh

to allow the script to be executable, and then type:

    $ ./Miniconda3-latest-Linux-x86_64.sh

This will install Miniconda3. Hold enter until you get to a yes/no prompt and type yes when asked.

You will now need to restart your system to finish the conda install. Open your terminal and before your prompt you should see (base) – this means conda has installed.

### Get Minikraken DB

Type:

    $ wget ftp://ftp.ccb.jhu.edu/pub/data/kraken2_dbs/old/minikraken2_v2_8GB_201904.tgz

This will download the kraken database that Catsup uses. Then type:

    $ tar xf minikraken2_v2_8GB_201904.tgz

This may take a little while. It will extract kraken into a directory:  minikraken2_v2_8GB_201904_UPDATE

### Install Catsup

If git is not installed:

Type:

    $ sudo apt install git

to install git.

Then type:

    $ git clone https://github.com/oxfordmmm/catsup

If you now type:
    $ ls

You should see a catsup directory.

Type:

    $ cd catsup

To enter the directory. Then type:

    $ conda env create -f environment.yml

To create the catsup environment. Type:

    $ conda activate catsup

This will activate the catsup environment. (base) before your prompt will change to (catsup)

### Install argh

Type
    $ pip3 install argh

To install a small dependency which Catsup uses.

### Edit config files

Type

    $ nano config.json-example-conda

This will open up the config file in nano editor (or use text editor of your choice)

If you are not using a cluster – remove “-process.executor slurm” from “nextflow_additional_params”.

You now need to edit the section below so the directories match your system, username and directory:

```
"catsup-kraken2": {
            "script": "/home/YOURUSERNAME/catsup/pipelines/catsup-kraken2/catsup-kraken2.nf",
            "image": "/home/YOURUSERNAME/miniconda3/envs/catsup",
            "human_ref": "/home/YOURUSERNAME/minikraken2_v2_8GB_201904_UPDATE"
```

Then you need to edit the “upload” section (seen below)

```
"upload":
    {
        "s3":
        {
            "bucket": "s3://mmm-sp3-alpha",
            "s3cmd-config": "/home/ubuntu/.s3cfg-catsup"
```

Delete the “bucket” and “S3cmd-config” lines and add “par_url” and your par key as provided by us – see below:

```
"upload": {
        "s3": {
            "par_url": “PAR KEY PROVIDED BY US"
```

Save the file then type:

    $ cp config.json-example-conda config.json

This will copy it to the config.json file that Catsup reads.

### Creating inputs.csv

Catsup needs to be executed 4 times to run its steps.

The first time we run it is to generate the inputs.csv file that will match the data you upload.

To run Catsup the first time type:

$ python3 catsup submission /home/username/fastqfolder

Where submission is the name of the folder you want Catsup to create your inputs.csv file in and /home/username/fastqfolder is the directory your sequencing data is in.

If you run the command with the directory in it the inputs.csv will try and automatically fill in some of the data.

### Editing inputs.csv

A directory will have been created (“submission”) and within it inputs.csv; the inputs.csv file need to be edited and verified.

“sample_name” should be edited to only contain the sample name

Example:

If your files are testsample_1.fastq.gz and testsample_2.fastq.gz then “sample_name” should be edited to testsample.

“sample_file_extension” should match the format that your file is being uploaded in, i.e fastq.gz or bam.

For paired end sequencing with 2 files per sample the inputs.csv is formatted as below:

Ensure rest of the metadata columns are updated and accurate.

### Running Catsup

Type:
    $ python3 catsup.py submission

This will run Catsup through the pre-processing steps. You should see something like:

Output:

```
*** Preprocessing step: prepare data

Preparing data for pipeline

testsubmission/inputs.csv validated

testsubmission/pipeline_in/2149752c-375f-4f47-9884-771d6a95c06d_1.fastq.gz -> /home/ubuntu/catsup-oxfordmmm/in/P0001_1.fastq.gz

testsubmission/pipeline_in/2149752c-375f-4f47-9884-771d6a95c06d_2.fastq.gz -> /home/ubuntu/catsup-oxfordmmm/in/P0001_2.fastq.gz

testsubmission/pipeline_in/46a76f9e-07a4-4646-a686-39351cf8c8d0_1.fastq.gz -> /home/ubuntu/catsup-oxfordmmm/in/P0002_1.fastq.gz

testsubmission/pipeline_in/46a76f9e-07a4-4646-a686-39351cf8c8d0_2.fastq.gz -> /home/ubuntu/catsup-oxfordmmm/in/P0002_2.fastq.gz

testsubmission/pipeline_in/4074a583-d5be-4c8c-b578-93623b110e94_1.fastq.gz -> /home/ubuntu/catsup-oxfordmmm/in/P0003_1.fastq.gz

testsubmission/pipeline_in/4074a583-d5be-4c8c-b578-93623b110e94_2.fastq.gz -> /home/ubuntu/catsup-oxfordmmm/in/P0003_2.fastq.gz

Wrote sp3 submission data to: testsubmission/sp3data.csv

Wrote sample file <-> uuid map to: testsubmission/sample_uuid_map.csv

*** Finished preprocessing step: prepare data
```
Type

    $ python3 catsup.py submission

again to run through the next step: nextflow pipeline. You should see something like:

Output:

```
*** Preprocessing step: nextflow pipeline

Running pipeline: catsup-kraken2

Changing directory to: testsubmission/pipeline_run

Nextflow invocation: nextflow /home/ubuntu/catsup-oxfordmmm/pipelines/catsup-kraken2/catsup-kraken2.nf --input_dir ../pipeline_in/ --read_pattern '*_{1,2}.fastq.gz' --output_dir ../upload -with-singularity /data/images/fatos-20200320T140813_2.2.img --db /data/databases/clockworkcloud/kraken2/minikraken2_v2_8GB_201904_UPDATE

*** Finished preprocessing step: nextflow pipeline

*** Next step: s3 upload
```

This step may take some time. Catsup assumes it has access to all memory on the system so be careful not to have other applications/browers running to avoid out of memory errors.

Type:

    $ python3 catsup.py submission

This will execute the final step which is the S3 upload. Once this is done you should get a prompt telling you it has completed. Your files will now have been pushed to the Oracle cloud GPAS database and are ready for processing through the analysis pipelines.
