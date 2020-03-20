#!/usr/bin/env nextflow

/* Command line example
nextflow catsup-kraken2.nf --input_dir /data/qc_test/ --read_pattern '*.{1,2}.fastq.gz' \
--db /data/references/minikraken2_v2_8GB_201904_UPDATE -with-singularity /data/images/fatos-20200319T151233_2.2.img \
--output_dir out -with-report -resume
*/

/* 
 * Display information before the run
*/
log.info "                         "
log.info """                   
------------------------------------
SP3 catsup-kraken2 nextflow pipeline
------------------------------------
- Trim using trim_galore
- Remove human reads using kraken2                         
--input_dir: 	$params.input_dir
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
* trim_galore --fastqc --paired ${read1} ${read2} 
*/

process process_trim {

    memory '1 GB'

    // publishDir "${output_dir}/trimmed_reads", pattern: '*_val_{1,2}.fq.gz', mode: 'copy'
    // publishDir "${output_dir}/fastqc", pattern: '*_fastqc.{zip,html}', mode: 'copy'
    // publishDir "${output_dir}/trim_galore" , pattern: '*_trimming_report.txt', mode: 'copy'

    echo true

    input:
    set dataset_id, read1, read2 from fqs

    output:
    set dataset_id, file("*_val_1.fq.gz"), file("*_val_2.fq.gz") into trim_out
    set file("*_trimming_report.txt"), file("*_fastqc.{zip,html}") into qc
    
    script:
    """
    #ls -al ${db}

    # TRIM BEGIN

    if [[ \$(zcat ${read1} | head -n4 | wc -l) -eq 0 ]]; then
      exit 0
    else
      trim_galore --fastqc --paired ${read1} ${read2}
    fi

    # TRIM END
    """
}

/***********
* PART 2: Identify human reads
* kraken2 --db ${db} --report ${kraken2_summary} --output ${kraken2_read_classification} --paired ${read1} ${read2}
*/


process classification {

    tag { dataset_id }

    memory '10 GB'

    //publishDir "${output_dir}/", mode: 'copy'

    input:
    set val(dataset_id), read1, read2 from trim_out

    output:
    set val(dataset_id), read1, read2, file("${dataset_id}.classification_non_human_read_list.txt") into non_human_list

    script:
    kraken2_summary              = "${dataset_id}.species_classification.txt"
    kraken2_read_classification  = "${dataset_id}.read_classification.txt"
    kraken2_human_read_list      = "${dataset_id}.classification_human_read_list.txt"
    kraken2_non_human_read_list  = "${dataset_id}.classification_non_human_read_list.txt"
    """
    cat <<- EOF >> filter.py
    import sys

    filename = sys.argv[1]

    tbl1 = open(filename).readlines()
    tbl1 = [x.split('\t') for x in tbl1]

    #
    # add missing indexes to sample reads 1-9 (bug in kraken2)
    # for whatever reason, in the kraken2 output the first 10 lines
    # don't have the .N ending. So if the 11th line has .12 we
    # add them back
    #
    if tbl1[11][1][:-3] == '.12':
        for i, row in enumerate(tbl1[0:9]):
            row[1] = f'{row[1]}.{i+1}'

    #
    # write non-human read ids
    #
    human_id = '9606'

    for row in tbl1:
        if row[2] != human_id:
            print(row[1])
    EOF

    kraken2 --db ${db} --report ${kraken2_summary} --output ${kraken2_read_classification} --paired ${read1} ${read2}
    
    echo "==== kraken2 ====" > ${kraken2_human_read_list}
    cat ${kraken2_summary} | grep 9606 >> ${kraken2_human_read_list}
    echo "==== human reads ====" >> ${kraken2_human_read_list}
    awk '\$3==\"9606\" { print \$2 }' ${kraken2_read_classification} >> ${kraken2_human_read_list}
    python3 filter.py ${kraken2_read_classification} > ${kraken2_non_human_read_list}
    
    rm -rf ${dataset_id}.read_classification.txt
    rm -rf ${dataset_id}.classification_human_read_list.txt
    rm -rf ${dataset_id}.species_classification.txt -rf ${dataset_id}.classification_human_read_list.txt
    rm -rf ${dataset_id}.species_classification.txt
    
    """
}

/***********
* PART 3: Remove human reads
* seqtk subseq ${dataset_id}_1.fix ${nonhm} | gzip > "${dataset_id}_C1.fastq.gz"
* seqtk subseq ${dataset_id}_2.fix ${nonhm} | gzip > "${dataset_id}_C2.fastq.gz"
*/

process contam_removal {

    tag { dataset_id }

    publishDir "${output_dir}/", mode: 'copy'

    input:
    set val(dataset_id), read1, read2, file(nonhm) from non_human_list

    output:
    file("${dataset_id}_C1.fastq.gz")
    file("${dataset_id}_C2.fastq.gz")

    script:
    """
    cat <<- EOF >> fixheaders.py
    import re
    import sys

    p = re.compile("^(@[^\\s]+)\\/([0-9]+)\$")

    prevLine = None

    for line in sys.stdin:
        m = p.match(line)
        if m and prevLine != "+\\n":
            sys.stdout.write(m.group(1) + '\\n')
        else:
            sys.stdout.write(line)
        prevLine = line
    EOF

    zcat ${read1} | python3 fixheaders.py | gzip > ${dataset_id}_1.fix
    zcat ${read2} | python3 fixheaders.py | gzip > ${dataset_id}_2.fix

    seqtk subseq ${dataset_id}_1.fix ${nonhm} | gzip > "${dataset_id}_C1.fastq.gz"
    seqtk subseq ${dataset_id}_2.fix ${nonhm} | gzip > "${dataset_id}_C2.fastq.gz"

    rm ${dataset_id}_1.fix
    rm ${dataset_id}_2.fix
    rm ${dataset_id}.classification_non_human_read_list.txt
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