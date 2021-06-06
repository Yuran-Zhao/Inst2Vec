import os

from utils import ORIGINAL_DATA_BASE, read_file


def write_file(data, filename):
    print("Writing data into {}...".format(filename))
    with open(filename, "w", encoding="utf-8") as fout:
        for sent in data:
            fout.write(sent.replace("<space>", "SPACE"))


def convert(fin, fout):
    print("Start the replacement task for {}...".format(fin))
    # filename = "/home/ming/malware/data/elfasm_inst_pairs/linux32_00xxxx.all"
    sents = read_file(fin)
    write_file(sents, fout)


def main():
    # for i in range(6):
    for i in [1]:
        fin = os.path.join(ORIGINAL_DATA_BASE, "linux32_0{}xxxx.all".format(i))
        fout = os.path.join(ORIGINAL_DATA_BASE, "inst.{}.pos.txt".format(i))
        convert(fin, fout)


if __name__ == "__main__":
    main()
