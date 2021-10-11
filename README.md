# Inst2Vec Model
Using [HuggingFace Transformers](https://github.com/huggingface/transformers) to train a BERT for Assemble Language from scratch. We name it `Inst2Vec` for it is designed to generate vectors for assemble instructions.

It is a part of the model we proposed in the paper [A Hierarchical Graph-based Neural Network for Malware Classification]().

The preprocessing procedure can be found in [process_data](./process_data/readme.md).

You can simply run `python train_my_tokenizer.py` to obtain an Assemble Tokenizer.

The script I use to train the `Inst2Vec1` model is as follows:
```
python my_run_mlm_no_trainer.py \
    --per_device_train_batch_size 8192 \
    --per_device_eval_batch_size 16384 \
    --num_warmup_steps 4000 --output_dir ./ \
    --seed 1234 --preprocessing_num_workers 32 \
    --max_train_steps 150000 \
    --eval_every_steps 1000
```