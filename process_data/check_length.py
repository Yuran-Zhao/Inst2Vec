import os
import  pdb
from utils import ORIGINAL_DATA_BASE, read_file


def check(filename):
    sents = read_file(filename)
    result = 0
    for sent in sents:
        result = max(result, len(sent[:-1].replace("\t", " ").split()))
    print("The longest sentence in {} has {} words".format(filename, result))
    return result


def main():
    longest = 0
    # for i in range(6):
    for i in range(10):
        for group in ("pos", "neg"):
            filename = os.path.join(
                ORIGINAL_DATA_BASE, "inst.{}.{}.txt.clean".format(i, group)
            )
            longest = max(check(filename), longest)
    print("The longest sentence in all files has {} words.".format(longest))


if __name__ == "__main__":
    main()

