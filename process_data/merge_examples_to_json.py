import gc
import json
import os
from multiprocessing import Pool, Process, Queue

from tqdm import tqdm

from utils import CURRENT_DATA_BASE, ORIGINAL_DATA_BASE, read_file

BASE = 4600000


def write_worker(sents, json_file, index):
    examples = []
    for sent in tqdm(sents):
        tmp = sent[:-1].split("\t")
        examples.append({"text": tuple(tmp[1:]), "is_next": int(tmp[0])})
        examples[-1]["text"] = tuple(examples[-1]["text"])

    print("Writing to {}...".format(json_file + "{}.json".format(index)))
    results = {"data": examples}
    with open(json_file + "{}.json".format(index), "w") as f:
        json.dump(results, f)


def merge_to_json(pos, neg, json_file):
    sents = read_file(pos)

    p = Pool(36)

    for i in range(64):
        p.apply_async(
            write_worker, args=(sents[i * BASE : (i + 1) * BASE], json_file, i,)
        )
    print("Waiting for all sub-processes done...")
    p.close()
    p.join()
    print("All subprocess done.")

    # length = len(sents)
    # base = length // 20000000 + 1

    # for i in tqdm(range(length)):
    #     examples = []
    #     tmp = sents[i][:-1].split("\t")
    #     examples.append({"text": tuple(tmp[1:]), "is_next": int(tmp[0])})
    #     examples[i]["text"] = tuple(examples[i]["text"])
    #     index = i // 20000000
    #     print("Writing to {}...".format(json_file + "{}.json".format(index)))
    #     with open(json_file + "{}.json".format(index), "w") as f:
    #         json.dump(examples, f)

    del sents
    gc.collect()

    sents = read_file(neg)

    p = Pool(8)

    for i in range(64):
        p.apply_async(
            write_worker, args=(sents[i * BASE : (i + 1) * BASE], json_file, 64 + i,)
        )
    print("Waiting for all sub-processes done...")
    p.close()
    p.join()
    print("All subprocess done.")

    # length = len(sents)
    # for i in tqdm(range(length)):
    #     examples = []
    #     tmp = sents[i][:-1].split("\t")
    #     examples.append({"text": tuple(tmp[1:]), "is_next": int(tmp[0])})
    #     examples[i]["text"] = tuple(examples[i]["text"])
    #     index = i // 20000000
    #     print("Writing to {}...".format(json_file + "{}.json".format(base + index)))
    #     with open(json_file + "{}.json".format(base + index), "w") as f:
    #         json.dump(examples, f)


def main():
    # for i in range(6):
    for i in [1]:
        pos = os.path.join(ORIGINAL_DATA_BASE, "inst.{}.pos.label.txt".format(i))
        neg = os.path.join(ORIGINAL_DATA_BASE, "inst.{}.neg.label.txt".format(i))
        json_file = os.path.join(CURRENT_DATA_BASE, "inst.{}.".format(i))
        merge_to_json(pos, neg, json_file)


if __name__ == "__main__":
    main()
