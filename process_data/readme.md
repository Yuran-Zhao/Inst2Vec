# Pre-processing steps
### 1. run `convert_space_format.py`
Convert the string `<space>` to `SPACE`

`linux32_0ixxxx.all -> inst.i.pos.txt` located at `/home/ming/malware/data/elfasm_inst_pairs`

### 2. remove the repete lines in the `inst.i.pos.txt`
Using python script is too slow. We use the shell instead.

``` shell
cat inst.i.pos.txt | sort -n | uniq > inst.i.pos.txt.clean
```


### 3. run `create_negtive_examples.py`
We use the next file of the current file as its negative examples, which is apparently rational.

Specifically, for each instruction in the current positive file, we randomly choose a line in its next file and select one of two instructions in the line as its negative example.

generate `inst.i.neg.txt` located at `/home/ming/malware/data/elfasm_inst_pairs`

### 4. run `merge_examples_to_json.py`
We dump the positive and negative examples with their corresponding labels into several json files. 
Each json file contains 20m lines of examples.

generate `inst.i.{0-127}.json` located at `/home/ming/malware/inst2vec_bert/data/asm_bert`

### 5. run `check_length.py`
We will specify the length padded to when we use the tokenizer, `tokenizer.enable_padding(..., length=)`. 

So we need to know the longest sentences in the dataset.

<!-- ### 5. run `count_word_for_vocab.py`
Similarly, we also need to specify the size of vocabulary when we train the tokenizer, `WordLevelTrainer(vocab_size=, ...)`. 

So we need to know how many characters in the dataset.

Something is wrong with `p.join()`, so I just set `vocab_size=2`. -->