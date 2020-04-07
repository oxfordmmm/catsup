#!/usr/bin/env nextflow

/* Command line example
nextflow catsup-research.nf --input_dir /data/qc_test/ --read_pattern '*.{1,2}.fastq.gz' --paired true \
--output_dir out -with-report -resume

nextflow catsup-research.nf --input_dir /data/nano/ --read_pattern '*_1.fastq.gz' --paired false \
--output_dir out -with-report -resume

*/

/*
 * Display information before the run
*/
log.info "                         "
log.info """
------------------------------------
SP3 catsup-research nextflow pipeline
------------------------------------
- Trim using trim_galore
- Remove human reads using kraken2
--input_dir: 	$params.input_dir
--read_pattern  $params.read_pattern
--paired        $params.paired
--output_dir    $params.output_dir
************************************
"""
log.info "                         "

/*
* Parse the input parameters
*/

input_dir = params.input_dir
read_pattern = params.read_pattern
output_dir = params.output_dir
paired = params.paired

if (paired == true)
    Channel.fromFilePairs(input_dir + read_pattern, flat:true).set { fqs_paired }
else{
    fqs = Channel.fromPath(input_dir + read_pattern)
                .map { file -> tuple(file.baseName.take(file.baseName.length() - 8), file) }
}

if (paired == true){

    process process_paired {

        tag { dataset_id }

        memory '1 GB'

        echo true

	publishDir "${output_dir}/", mode: 'copy'

        input:
        set dataset_id, read1, read2 from fqs_paired

        output:
        set dataset_id, read1, read2 into output

	script:
	"""
        ln -s "${read1}" "${dataset_id}_C1.fastq.gz"
        ln -s "${read2}" "${dataset_id}_C2.fastq.gz"
        """
	
    }
}
else{
    process process_single {

    tag { dataset_id }
    memory '1 GB'

    echo true

    publishDir "${output_dir}/", mode: 'copy'

    input:
    set dataset_id, read1 from fqs

    output:
    file("${dataset_id}_C1.fastq.gz")

    script:
    """
    ln -s "${read1}" "${dataset_id}_C1.fastq.gz"
    """
    }
}

/*
 * Display information about the completed run
 */
workflow.onComplete {
    log.info "************************************"
    log.info "Nextflow Version: $workflow.nextflow.version"
    log.info "Command line: $workflow.commandLine"
    log.info "Container:    $workflow.container"
    log.info "Duration: $workflow.duration"
    log.info "Output data directory: $params.output_dir"
}
