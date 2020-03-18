# Catsup
Catsup is a python script for SP3 users to pre-processing local pathogen sequencing data and upload data to a data storage (S3 bucket) for SP3 to process.

# what does catsup do?

### Prepare the template
1. Generates a template for data submission
2. Validates the template after user input

### Anonymizing sample identifier
3. Creates unique identifier (guid) for submission
4. Creates unique identifier (guid) for every sample
5. Generate md5sum for each sample file
6. Upldate the template with submission guid, sample guid and md5sum
7. Rename/symlink sample files with sample guid
8. Generates a lookup table of sample name and sample guid

### Removing human reads
9. Run quality control pipeline (trimming and remove human reads)

### Upload to a S3 bucket
10. Upload cleaned (no human reads) sample files to S3 buckets
