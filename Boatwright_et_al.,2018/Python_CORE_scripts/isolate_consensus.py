# -*- coding: utf-8 -*-
"""
Created on Fri Apr 28 10:35:53 2017

@author: Lucas Boatwright
"""

from sys import argv, stderr
import argparse
from datetime import datetime
import Bio.AlignIO
from Bio.Align import AlignInfo
import subprocess as sp
from glob import glob
from itertools import chain

def parse_arguments():
    """Parse arguments passed to script"""
    parser = argparse.ArgumentParser(description=
    "This script receives 'grouped_hits.txt', uses a FASTA file to get the \
    \nsequences, uses MAFFT to align each group, then generates a consensus \
    \nsequence for each group using biopython.\n\n \
    Example: python {0} -g grouped_hits.txt -f sequences.fasta".format(argv[0]),
    formatter_class = argparse.RawDescriptionHelpFormatter)
    
    requiredNamed = parser.add_argument_group('required arguments')

    requiredNamed.add_argument("-g", "--GROUPS", type=str, required=True,\
    help="Grouped hits file generated by group_self_BLAST.py", action="store")

    requiredNamed.add_argument("-f", "--FASTA", type=str, required=True,\
    help="FASTA file containing all sequences.", action="store")

    return parser.parse_args() 
    
    
def fasta_to_dict(fasta_file):
    """Consolidate deflines and sequences from FASTA as dictionary"""
    deflines = []
    sequences = []
    sequence = ""
    with open(fasta_file, "r") as file:
        for line in file:
                if line.startswith(">"):
                        deflines.append(line.rstrip().lstrip('>'))
                        if sequence:
                                sequences.append(sequence)
                                sequence = ""
                else:
                        sequence += line.rstrip()
        sequences.append(sequence)
    fasta_dict = {}
    for x, defline in enumerate(deflines):
        fasta_dict[defline]=sequences[x]
    return fasta_dict


def isolate_consensus(groups, fasta):
    """Perform multiple sequence alignment and isolate consensus from each 
    group in grouped_hits.txt"""
    with open(groups,"r") as f:
        file = f.readlines()

    sequences_in_out = open("sequences_in_out.table","w")
    consensus_sequences = open("consensus_sequences.fasta","w")

    for consensus_num, line in enumerate(file):
        group_sequences = line.rsplit()
        open("temp_sequences","w").close()
        # Write group of sequences to temporary file
        for group in group_sequences:
            sequences_in_out.write("{0}\t".format(group))
            with open("temp_sequences",'a') as output:
                output.write(">{0}\n{1}\n".format(group, fasta[group]))
        # Run MAFFT alignment
        sp.call(['/apps/mafft/7.127/bin/mafft', '--adjustdirection', 
                 '--clustalout', '--preservecase', 'temp_sequences'],
                 stdout=open('temp_alignment.txt','w'), 
                 stderr=open('temp_mafft_log','w') )
        # cat MAFFT log files
        sp.call(['cat','temp_mafft_log'], 
                stdout = open("all_alignments.log",'a+'))
        # cat MAFFT alignment files
        sp.call(['cat','temp_alignment.txt'], 
                stdout = open("all_alignments.faa",'a+'))

        #output group_sequences and the consensus generated in a file
        sequences_in_out.write("||\t>Consensus_{0}\n".format(consensus_num + 1))
        align=Bio.AlignIO.read("temp_alignment.txt","clustal")
        summary_align = AlignInfo.SummaryInfo(align)
        consensus = summary_align.dumb_consensus(threshold=0.51, ambiguous='N')
        consensus_sequences.write(">Consensus_{0}\n{1}\n".format(
                                            consensus_num + 1,consensus))
    sequences_in_out.close()
    temp_files = glob("*temp*")
    sp.call(['rm'] + temp_files)
    
    
def isolate_ungrouped_contigs(fasta_dict, groups):
    """Determine which transcripts were not grouped and concatenate both
    contigs_collapsed.fasta and ungrouped contigs into new transcriptome"""
    with open(groups) as f:
        grouped_contigs = list(chain.from_iterable(
                                [i.split() for i in f.readlines()]
                                                    )
                                )
    db_deflines = fasta_dict.keys()
    ungrouped_contigs = [i for i in db_deflines if i not in grouped_contigs]
    with open("ungrouped_contigs.fasta",'w') as output:
        for contig in ungrouped_contigs:
            output.write(">{0}\n{1}\n".format(contig, fasta_dict[contig]))   
    sp.call(['cat','consensus_sequences.fasta','ungrouped_contigs.fasta'], 
            stdout=open("full_assembly_after_consensus.fasta",'w'))
        
    
if __name__ == "__main__":
    start = datetime.now()
    args = parse_arguments()
    stderr.write("Executed: python {0} -g {1} -d {2}\n".format(argv[0], 
                                                 args.GROUPS, args.FASTA))
                                                 
    stderr.write("Reading FASTA to dictionary.\n")
    fasta_dict = fasta_to_dict(args.FASTA)                                             
                                                 
    stderr.write("Starting compression loops.\n")                                             
    isolate_consensus(args.GROUPS, fasta_dict)

    stderr.write("Finalizing FASTA.\n")
    isolate_ungrouped_contigs(fasta_dict, args.GROUPS)
    
    stop = datetime.now()
    stderr.write("Runtime: {0}\n".format(str(stop - start)))
