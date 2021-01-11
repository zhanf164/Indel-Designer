#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 25 20:26:22 2020

@author: zhanf
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 23 12:43:19 2020

@author: zhanf
"""

import argparse
from Bio.Seq import Seq
from Bio import SeqIO
import sys
import os


parser = argparse.ArgumentParser()
parser.add_argument('infile', help='vcf which contains your indel information')
parser.add_argument('outfile', help='The outfile which you want baits written to.')
parser.add_argument('--s' , dest='strand', action='store_true', help='if strand info is available in the 5th column, include this parameter')
parser.add_argument('genome', help= 'The genome you want to extract baits from')

args = parser.parse_args()

def revcomp(string):
    '''
    Simple revcomp function.
    '''
    seq = Seq(string)
    return str(seq.reverse_complement())

def gather_info(infile, s):
    '''
    This function just takes in the infile, as well as a boolean that should be autogenerated based on what
    commmands were provided to the script on the commmand line. if stranded parameter is used, then the output 
    will be a dictionary where the key is the choromosome and a position, and the value is a list of length 3
    where the first element is the strand, the second element is the reference allele, and the last is the variant, 
    if the s parameter is false, then the output dict value will only contain the reference allele and variant (thus be len of 2)
    
    '''
    variant_dict = {}
    with open(infile, 'r') as f:
        for line in f:
            k  = line.split('\t')[0] + '-' + line.split('\t')[1] # lets make the key the chromosome and variant position
            if s:
                v = [line.split('\t')[4]]
                v.append(line.split('\t')[5])
                v.append(line.split('\t')[6].split(','))
                variant_dict[k] = v
            else:
                v = [] # if no strand info, just start with an empty list
                v.append(line.split('\t')[5])
                v.append(line.split('\t')[6].split(','))
                variant_dict[k] = v
    return variant_dict


def make_ref_padded_bait(seq_dict, chromo, start, ref, variant):
    offset = len(ref) #the reference allele in the sam file may be longer than one nucl, but the "variant position" is only one nt, so we need to pad by this length.
    second_bait_start = start + offset
    bait_first_half =  seq_dict[chromo].seq[start-40:start-1]
    indel = variant
    length_left_to_add = 80-(len(bait_first_half) + len(indel))-1
    bait_second_half = seq_dict[chromo].seq[second_bait_start-1:second_bait_start+length_left_to_add]    
    return bait_first_half, bait_second_half, bait_first_half + indel + bait_second_half

def make_non_padded_bait(seq_dict, chromo, start, ref, variant):
    bait_first_half =  seq_dict[chromo].seq[start-40:start-1]
    indel = variant
    len_left_to_add = 80-(len(bait_first_half)+ len(indel))
    bait_second_half = seq_dict[chromo].seq[start:start+len_left_to_add]
    return bait_first_half, bait_second_half, bait_first_half + indel + bait_second_half

def Diagnostic_Printing(key, start, seq_dict, chromo, bait_first_half, bait_second_half, bait, value, val):
    print(key)
    print("Normal Region: {}".format(seq_dict[chromo].seq[start-40:start+40]))
    print("First Half: {}".format(bait_first_half))
    print("Second Half: {}".format(bait_second_half))
    print("Normal_allele: {}".format(value[1]))
    print("Variant Bait: {}".format(bait))
    print("Intended variant: {}".format(val))
    print(len(bait))

    
def Get_Genomic_regions_and_Make_Baits(genome, variant_dict, s):
    seq_dict = SeqIO.to_dict(SeqIO.parse(genome, 'fasta'))
    out_dict = {}
    for key, value in variant_dict.items():
        chromo = key.split('-')[0]
        start = int(key.split('-')[1]) #position of the variant
        if s:
            if value[0] == '+':#Positive strand is easy, just take whats in the genome, will handle - strand later
                for val in value[2]: # there are two different scenarios, insertion or deletion, need to handle both
                    if len(val) > len(value[1]):#this will be an insertion since variant is longer than reference
                        if len(value[1]) > 1:#in the case that the length of the reference allele is greater than 1, we need to pad the second half of the bait so that we aren't repeating sequence that is already there. This is becuase the vcf file only gives us a single postiion where the variant starts, but in some cases, the len of the reference supplied is greater than this one position.  
                            bait_first_half, bait_second_half, bait = make_ref_padded_bait(seq_dict, chromo, start, value[1], val)
                            Diagnostic_Printing(key, start, seq_dict, chromo, bait_first_half, bait_second_half, bait, value, val)
                            out_dict[key + '-' + val] = bait
                        else:
                            bait_first_half, bait_second_half, bait = make_non_padded_bait(seq_dict, chromo, start, value[1], val) #This is the only case we dont need to pad since the reference allele is only 1bp, which corresponds to the coordinant of the variant
                            Diagnostic_Printing(key, start, seq_dict, chromo, bait_first_half, bait_second_half, bait, value, val)
                            out_dict[key + '-' + val] = bait
                    elif len(val) < len(value[1]):
                        bait_first_half, bait_second_half, bait = make_ref_padded_bait(seq_dict, chromo, start, value[1], val)
                        Diagnostic_Printing(key, start, seq_dict, chromo, bait_first_half, bait_second_half, bait, value, val)
                        out_dict[key + '-' + val] = bait
                    else:
                        sys.exit("Vairant is not an indel, since its the same length as reference.") # this should never happen
            else:
                for val in value[2]:
                    if len(val) > len(value[1]):#this will be an insertion since variant is longer than reference
                        if len(value[1]) > 1:#in the case that the length of the reference allele is greater than 1, we need to pad the second half of the bait so that we aren't repeating sequence that is already there. This is becuase the vcf file only gives us a single postiion where the variant starts, but in some cases, the len of the reference supplied is greater than this one position.  
                            bait_first_half, bait_second_half, bait = make_ref_padded_bait(seq_dict, chromo, start, value[1], val)
                            Diagnostic_Printing(key, start, seq_dict, chromo, bait_first_half, bait_second_half, bait, value, val)
                            out_dict[key + '-' + val] = bait
                        else:
                            bait_first_half, bait_second_half, bait = make_non_padded_bait(seq_dict, chromo, start, value[1], val) #This is the only case we dont need to pad since the reference allele is only 1bp, which corresponds to the coordinant of the variant
                            Diagnostic_Printing(key, start, seq_dict, chromo, bait_first_half, bait_second_half, bait, value, val)
                            out_dict[key + '-' + val] = bait
                    elif len(val) < len(value[1]):
                        bait_first_half, bait_second_half, bait = make_ref_padded_bait(seq_dict, chromo, start, value[1], val)
                        Diagnostic_Printing(key, start, seq_dict, chromo, bait_first_half, bait_second_half, bait, value, val)
                        out_dict[key + '-' + val] = bait
                    else:
                        sys.exit("Vairant is not an indel, since its the same length as reference.")
    return out_dict  


def Write_out(out_dict, outfile):
    current_dir = os.getcwd()
    outpath = os.path.join(current_dir, outfile)
    with open(outpath, 'w') as f:
        for key, value in out_dict.items():
            f.write('>' + key + '\n')
            f.write(str(value) + '\n')
                
if __name__ == '__main__':
    if args.strand:
        variant_dict = gather_info(args.infile, args.strand)
        out_dict = Get_Genomic_regions_and_Make_Baits(args.genome, variant_dict, args.strand)
        Write_out(out_dict, args.outfile)
    else:
        gather_info(args.infile, False)
