import os
from multiprocessing import Pool, Process, Queue

from tqdm import tqdm

from utils import ORIGINAL_DATA_BASE, read_file

q = Queue(128)
BASE = 4600000


def counter_worker(sents):
    cnt = set()
    for sent in tqdm(sents):
        cnt = cnt.union(set(sent[:-1].replace("\t", " ").split()))
    print("Process {} get {} words".format(os.getpid(), len(cnt)))
    q.put(cnt)
    return


def counter(filename):
    sents = read_file(filename)

    p = Pool(36)

    for i in range(64):
        p.apply_async(counter_worker, args=(sents[i * BASE : (i + 1) * BASE],))
    print("Waiting for all sub-processes done...")
    p.close()
    p.join()
    print("All subprocess done.")
    cnt = set()
    # for sent in tqdm(sents):
    #     cnt += set(sent[-1].replace("\t", " ").split())
    for _ in tqdm(range(64)):
        cnt = cnt.union(q.get())
    print("There are {} charcters in {}".format(len(cnt), filename))
    return cnt


def main():
    cnt = set()
    # for i in range(6):
    for i in [1]:
        for group in ["pos", "neg"]:
            filename = os.path.join(
                ORIGINAL_DATA_BASE, "inst.{}.{}.txt".format(i, group)
            )
            cnt += counter(filename)
    print("There are {} charcters in all files".format(len(cnt)))


if __name__ == "__main__":
    main()
