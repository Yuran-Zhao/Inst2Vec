from utils import ORIGINAL_DATA_BASE, read_file, write_file
from tqdm import tqdm 
import os

def remove(pos_file, neg_file):
    pos = read_file(pos_file)
    neg = read_file(neg_file)
    rets = []
    for n in tqdm(neg):
        if n in pos:
            continue
        rets.append(n)
    write_file(rets, neg_file)

def main():
    pos_file = os.path.join(ORIGINAL_DATA_BASE, "inst.all.pos.txt.clean")
    neg_file = os.path.join(ORIGINAL_DATA_BASE, "inst.all.neg.txt.clean")
    remove(pos_file, neg_file)

if __name__ == "__main__":
    main()
