import os

ORIGINAL_DATA_BASE = "/home/ming/malware/data/elfasm_inst_pairs"
CURRENT_DATA_BASE = "/home/ming/malware/inst2vec_bert/data/asm_bert"


def read_file(filename):
    print("Reading data from {}...".format(filename))
    with open(filename, "r", encoding="utf-8") as fin:
        return fin.readlines()

