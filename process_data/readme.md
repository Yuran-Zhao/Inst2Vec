# Pre-processing steps
### 1. run `convert_space_format.py`
Convert the string `<space>` to `SPACE`

### 2. run `create_negtive_examples.py`
We use the next file of the current file as its negative examples, which is apparently rational.

Specifically, for each instruction in the current positive file, we randomly choose a line in its next file and select one of two instructions in the line as its negative example.

### 3. run `merge_examples_to_json.py`
We dump the positive and negative examples with their corresponding labels into several json files. 
Each json file contains 20m lines of examples.

### 4. run `check_length.py`
We will specify the length padded to when we use the tokenizer, `tokenizer.enable_padding(..., length=)`. 

So we need to know the longest sentences in the dataset.

### 5. run `count_word_for_vocab.py`
Similarly, we also need to specify the size of vocabulary when we train the tokenizer, `WordLevelTrainer(vocab_size=, ...)`. 

So we need to know how many characters in the dataset.