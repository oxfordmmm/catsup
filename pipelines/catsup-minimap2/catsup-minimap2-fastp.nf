#!/usr/bin/env nextflow

/* Command line example:

nextflow catsup-minimap2-fastp.nf \
--input_dir data/qc_test/ \
--read_pattern '*.{1,2}.fastq.gz' \
--db /home/ndm.local/weig/catsup_kraken/db/minikraken2_v2_8GB_201904_UPDATE \
--output_dir out \
-with-report \
-with-singularity /home/ndm.local/weig/images/fastp.simg -resume

*/

/* 
 * Display information before the run
*/
log.info "                          "
log.info """                   
-------------------------------------
SP3 catsup-minimap2 nextflow pipeline
-------------------------------------
- Trim using fastp
- Remove human reads using minimap2                        
--input_dir: 	  $params.input_dir
--read_pattern  $params.read_pattern
--db            $params.db
--output_dir    $params.output_dir
************************************
"""
log.info "                         "

/*
* Parse the input parameters
*/

input_dir = params.input_dir
read_pattern = params.read_pattern
db = file(params.db)
output_dir = params.output_dir

Channel.fromFilePairs(input_dir + read_pattern, flat:true).set { fqs }

/***********
* PART 1: 
* fastp -i in.fq -o out.fq
* fastp -i in.R1.fq.gz -I in.R2.fq.gz -o out.R1.fq.gz -O out.R2.fq.gz
************/

process process_trim {

    tag { dataset_id }
    
    memory '1 GB'

    echo true

    // publishDir "${output_dir}/trimmed_reads", pattern: '*_val_{1,2}.fq.gz', mode: 'copy'
    // publishDir "${output_dir}/fastqc", pattern: '*_fastqc.{zip,html}', mode: 'copy'
    // publishDir "${output_dir}/trim_galore" , pattern: '*_trimming_report.txt', mode: 'copy'

    input:
    set dataset_id, file(forward), file(reverse) from fqs

    output:
    set dataset_id, file("*_val_1.fq.gz"), file("*_val_2.fq.gz") into trim_out
    set file("*_trimming_report.txt"), file("*_fastqc.{zip,html}") into qc

    script:
    """
    #ls -al ${db}

    # TRIM BEGIN

    if [[ \$(zcat ${forward} | head -n4 | wc -l) -eq 0 ]]; then
      exit 0
    else
      fastp -i ${forward} -I ${reverse} -o out_val_1.fq.gz -O out_val_2.fq.gz
    fi

    # TRIM END
    """
}

/***********
* PART 2: Remove human reads using minimap2 and samtools
************/


process process_deplete {

    tag { dataset_id }
   
    memory '10 GB'

    echo true

    publishDir "${params.output_dir}", mode: 'copy'

    input:
    set dataset_id, file(forward), file(reverse) from trim_out

    output:
    file("${dataset_id}_C1.fastq.gz")
    file("${dataset_id}_C2.fastq.gz")

    script:
    """
    # DEPLETE BEGIN

    minimap2 -ax sr ${db} ${forward} ${reverse} | \\
    tee >(samtools view -b -f 4 -F 264 - | samtools sort -o unmapped1.sorted.bam ) \\
    >(samtools view -b -f 8 -F 260 - | samtools sort -o unmapped2.sorted.bam ) \\
    >(samtools view -b -f 12 -F 256 - | samtools sort -o unmapped3.sorted.bam ) | \\
    samtools  view -b -F 4 - | samtools sort - | samtools fastq -N -1 ${forward}_human.R1.fq.gz -2 ${reverse}_human.R2.fq.gz -

    samtools merge merged.bam unmapped?.sorted.bam
    samtools fastq -N -1 ${dataset_id}_C1.fastq.gz -2 ${dataset_id}_C2.fastq.gz merged.bam

    # DEPLETE END
    """
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