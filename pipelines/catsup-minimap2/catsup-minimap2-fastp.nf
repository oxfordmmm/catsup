#!/usr/bin/env nextflow

/* Command line example:

./nextflow catsup-minimap2-fastp.nf \
--input_dir /home/ndm.local/weig/catsup/data/qc_test/ \
--read_pattern '*.{1,2}.fq.gz' \
--db /home/ndm.local/weig/catsup_kraken/db/minikraken2_v2_8GB_201904_UPDATE \
--output_dir /home/ndm.local/weig/catsup/out \
-with-report \
-with-singularity /home/ndm.local/weig/fatos/fatos.img

./nextflow catsup-minimap2-fastp.nf \
--input_dir /home/ndm.local/weig/catsup/data/qc_test/ \
--read_pattern '*_C{1,2}.fastq.gz' \
--db /home/ndm.local/weig/catsup_kraken/db/minikraken2_v2_8GB_201904_UPDATE \
--output_dir /home/ndm.local/weig/catsup/out \
-with-report \
-with-singularity /home/ndm.local/weig/fatos/fatos.img

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
* fastp \
*   -i human100k.1.fq.gz \
*   -I human100k.2.fq.gz \
*   -o human100k.1.out.fq.gz \
*   -O human100k.2.out.fq.gz \
*   --unpaired1 unpaired_out.fq.gz \
*   --unpaired2 unpaired_out.fq.gz \
*   -h fastp.html \
*   -j fastp.json \
*   --length_required 50 \
*   --cut_tail \
*   --cut_tail_window_size 1 \
*   --cut_tail_mean_quality 20
*
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
      fastp \
        -i ${forward} \
        -I ${reverse} \
        -o out_val_1.fq.gz \
        -O out_val_2.fq.gz \
        --unpaired1 unpaired_out.fq.gz \
        --unpaired2 unpaired_out.fq.gz \
        -h out_fastqc.html \
        -j out_trimming_report.json \
        --length_required 50 \
        --cut_tail \
        --cut_tail_window_size 1 \
        --cut_tail_mean_quality 20
      
      mv out_trimming_report.json out_trimming_report.txt
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