import os
from random import randint

from tqdm import tqdm

from utils import ORIGINAL_DATA_BASE, read_file


def create(pos, neg, tgt):
    pos_sents = read_file(pos)

    neg_sents = read_file(neg)
    neg_length = len(neg_sents)
    print("Start writing negative examples to {}...".format(tgt))
    with open(tgt, "w", encoding="utf-8") as fout:
        for sent in tqdm(pos_sents):
            first = sent.split("\t")[0]
            index = randint(0, neg_length - 1)
            pair = neg_sents[index].split("\t")[randint(0, 1)].replace("\n", "")
            fout.write(first + "\t" + pair + "\n")


def main():
    # for i in range(6):
    for i in range(10):
        j = (i + 1) % 10
        # neg = os.path.join(ORIGINAL_DATA_BASE, "linux32_0{}xxxx.all".format(j))
        # pos = os.path.join(ORIGINAL_DATA_BASE, "linux32_0{}xxxx.all".format(i))
        pos = os.path.join(ORIGINAL_DATA_BASE, "inst.{}.pos.txt.clean".format(i))
        neg = os.path.join(ORIGINAL_DATA_BASE, "inst.{}.pos.txt.clean".format(j))
        tgt = os.path.join(ORIGINAL_DATA_BASE, "inst.{}.neg.txt".format(i))
        create(pos, neg, tgt)


if __name__ == "__main__":
    main()
