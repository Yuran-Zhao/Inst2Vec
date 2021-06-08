# Pre-processing steps
### 1. run `convert_space_format.py`
Convert the string `<space>` to `SPACE`

`linux32_0ixxxx.all -> inst.i.pos.txt` located at `/home/ming/malware/data/elfasm_inst_pairs`

### 2. remove the repete lines in the `inst.i.pos.txt`
Using python script is too slow. We use the shell instead.

``` shell
cat inst.i.pos.txt | sort -n | uniq > inst.i.pos.txt.clean
```


### 3. create_negtive_examples
We use the next file of the current file as its negative examples, which is apparently rational.

Specifically, for each instruction in the current positive file, we randomly choose a line in its next file and select one of two instructions in the line as its negative example.

`python create_negtive_examples.py`, generating `inst.i.neg.txt` located at `/home/ming/malware/data/elfasm_inst_pairs`


### 4. merge all of the files
We catenate all of the `inst.i.pos.txt.clean` files and remove the possible repeting lines between different files:
``` shell
cat inst.*.pos.txt.clean | sort -n | uniq > inst.all.pos.txt.clean
```

We process the files containing negative examples similarly.
``` shell
cat inst.*.neg.txt.clean | sort -n | uniq > inst.all.neg.txt.clean
```

Based on the `inst.all.pos.txt.clean`, we remove the lines from `inst.all.neg.txt.clean` if they also occur in `inst.all.pos.txt.clean`. This can be completed by `python clean.py`.


### 5. convert to json format
We first add labels for positive examples and negative examples
```shell
cat inst.all.neg.txt.clean | sed 's/^/0\t&/g' > inst.all.neg.txt.clean.label
cat inst.all.pos.txt.clean | sed 's/^/1\t&/g' > inst.all.pos.txt.clean.label
```

We dump the positive and negative examples with their corresponding labels into several json files, using `python merge_examples_to_json.py`.

Generate `inst.all.{0,1}.json` located at `/home/ming/malware/inst2vec_bert/data/asm_bert`.


### 6. get the maximum of length in examples
We will specify the length padded to when we use the tokenizer, `tokenizer.enable_padding(..., length=)`. 

So we need to know the longest sentences in the dataset.

The result is `28`, so I set `length=32`


### 7. get the size of vocab of examples
Similarly, we also need to specify the size of vocabulary when we train the tokenizer, `WordLevelTrainer(vocab_size=, ...)`. 

So we need to know how many characters in the dataset.

The result is `1016`, so I set `vocab_size=2000`.