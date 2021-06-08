import argparse
import logging
import math
import os
import random

import datasets
import numpy as np
import tokenizers
import torch
import transformers
from accelerate import Accelerator
from datasets import load_dataset
from torch.nn import DataParallel
from torch.utils.data.dataloader import DataLoader
from tqdm.auto import tqdm
from transformers import (
    CONFIG_MAPPING,
    MODEL_MAPPING,
    AdamW,
    AutoConfig,
    AutoModelForMaskedLM,
    AutoTokenizer,
    BatchEncoding,
    BertConfig,
    BertForPreTraining,
    DataCollatorForLanguageModeling,
    SchedulerType,
    get_scheduler,
    set_seed,
)

from my_data_collator import MyDataCollatorForPreTraining
from process_data.utils import CURRENT_DATA_BASE

model_file = os.path.join(CURRENT_DATA_BASE, "bert-L2-H8.bin")
config_file = os.path.join(CURRENT_DATA_BASE, "bert-L2-H8.config.json")
tokenizer_file = os.path.join(CURRENT_DATA_BASE, "tokenizer-inst.all.json")


def load_model():
    config = BertConfig.from_json_file(config_file)
    model = BertForPreTraining(config)
    state_dict = torch.load(model_file)
    model.load_state_dict(state_dict)
    model.eval()
    print("Load model successfully !")

    tokenizer = tokenizers.Tokenizer.from_file(tokenizer_file)
    tokenizer.enable_padding(
        pad_id=tokenizer.token_to_id("[PAD]"), pad_token="[PAD]", length=32
    )
    print("Load tokenizer successfully !")
    return model, tokenizer


def process_input(inst, tokenizer):
    encoded_input = {}
    if isinstance(inst, str):
        # make a batch by myself
        inst = [inst for _ in range(8)]
    results = tokenizer.encode_batch(inst)
    encoded_input["input_ids"] = [result.ids for result in results]
    encoded_input["token_type_ids"] = [result.type_ids for result in results]
    encoded_input["special_tokens_mask"] = [
        result.special_tokens_mask for result in results
    ]

    # print(encoded_input["input_ids"])

    # use `np` rather than `pt` in case of reporting of error
    batch_output = BatchEncoding(
        encoded_input, tensor_type="np", prepend_batch_axis=False,
    )

    # print(batch_output["input_ids"])

    # NOTE: utilize the "special_tokens_mask",
    # only work if the input consists of single instruction
    length_mask = 1 - batch_output["special_tokens_mask"]

    data_collator = MyDataCollatorForPreTraining(tokenizer=tokenizer, mlm=False)

    model_input = data_collator([batch_output])

    # print(model_input["input_ids"])

    return model_input, length_mask


def generate_inst_vec(inst, method="mean"):
    model, tokenizer = load_model()

    model_input, length_mask = process_input(inst, tokenizer)
    length_mask = torch.from_numpy(length_mask).to(model_input["input_ids"].device)

    output = model(**model_input, output_hidden_states=True)

    if method == "cls":
        if isinstance(inst, str):
            return output.hidden_states[-1][0][0]
        elif isinstance(inst, list):
            return output.hidden_states[-1, :, 0, :]
    elif method == "mean":
        result = output.hidden_states[-1] * torch.unsqueeze(length_mask, dim=-1)
        # print(result.shape)
        if isinstance(inst, str):
            result = torch.mean(result[0], dim=0)
        elif isinstance(inst, list):
            result = torch.mean(result, dim=1)
        return result
    elif method == "max":
        result = output.hidden_states[-1] * torch.unsqueeze(length_mask, dim=-1)
        # print(result.shape)
        if isinstance(inst, str):
            result = torch.max(result[0], dim=0)
        elif isinstance(inst, list):
            result = torch.max(result, dim=1)
        return result


def main():
    inst = ["mov ebp esp" for _ in range(8)]
    print(generate_inst_vec(inst).shape)


if __name__ == "__main__":
    main()
