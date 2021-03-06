#!/bin/bash
#PBS -M polvadore@ufl.edu
#PBS -m n
#PBS -q bio
#PBS -r n
#PBS -j oe
#PBS-o /bio/mcintyre/trago/scripts/fastqc/PBS_LOGS/
#PBS -l walltime=01:00:00
#PBS -l nodes=1:ppn=4
#PBS -l pmem=5gb
#PBS -t 1-54

module load python

### set directories
PROJ=/bio/mcintyre/trago
ALNS=$PROJ/ercc_alignments/diploid
REF=/bio/mcintyre/references/ERCC_Ambion

#### I am using an SGE Array (pulls out each name from the file and calls it 'design')
DESIGN_FILE=$PROJ/outfiles/fastqc/diploids/design_files/list_trago_dip_untrim_fq.txt
DESIGN=$(cat $DESIGN_FILE | head -n $PBS_ARRAYID | tail -n 1)  #steps through file_list.txt by row
ID=$(basename "$DESIGN")

#calculate rpkm for reads aligning to ERCC92 controls 
python $PROJ/scripts/fastqc/rpkm_calculate.py -b $REF/ERCC92_v2.bed -m $ALNS/pileups/${ID}_ERCC.pileup -s $ALNS/aln_ERCC_${ID}.sam -o $ALNS/rpkm_count/counts_ERCC_${ID}.csv

