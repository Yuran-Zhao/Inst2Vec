from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
    Union,
)

import numpy as np
import tokenizers
import torch
from transformers import BatchEncoding

EncodedInput = List[int]


@dataclass
class MyDataCollatorForPreTraining:
    # """
    # Data collator used for language modeling. Inputs are dynamically padded to the maximum length of a batch if they
    # are not all of the same length.

    # Args:
    #     # tokenizer (:class:`~transformers.PreTrainedTokenizer` or :class:`~transformers.PreTrainedTokenizerFast`):

    #     tokenizer (:class:`tokenizers.Tokenizer`)
    #         The tokenizer used for encoding the data.
    #     mlm (:obj:`bool`, `optional`, defaults to :obj:`True`):
    #         Whether or not to use masked language modeling. If set to :obj:`False`, the labels are the same as the
    #         inputs with the padding tokens ignored (by setting them to -100). Otherwise, the labels are -100 for
    #         non-masked tokens and the value to predict for the masked token.
    #     mlm_probability (:obj:`float`, `optional`, defaults to 0.15):
    #         The probability with which to (randomly) mask tokens in the input, when :obj:`mlm` is set to :obj:`True`.
    #     pad_to_multiple_of (:obj:`int`, `optional`):
    #         If set will pad the sequence to a multiple of the provided value.

    # .. note::

    #     For best performance, this data collator should be used with a dataset having items that are dictionaries or
    #     BatchEncoding, with the :obj:`"special_tokens_mask"` key, as returned by a
    #     :class:`~transformers.PreTrainedTokenizer` or a :class:`~transformers.PreTrainedTokenizerFast` with the
    #     argument :obj:`return_special_tokens_mask=True`.
    # """
    # def __init__(
    #     self,
    #     tokenizer: tokenizers.Tokenizer,
    #     mlm: bool = True,
    #     mlm_probability: float = 0.15,
    #     pad_to_multiple_of: Optional[int] = None,
    # ):
    #     self.tokenizer = tokenizer
    #     self.mlm = mlm
    #     self.mlm_probability = mlm_probability
    #     self.pad_to_multiple_of = pad_to_multiple_of
    tokenizer: tokenizers.Tokenizer
    mlm: bool = True
    mlm_probability: float = 0.15
    pad_to_multiple_of: Optional[int] = None

    def __post_init__(self):
        if self.mlm and self.tokenizer.token_to_id("[MASK]") is None:
            raise ValueError(
                "This tokenizer does not have a mask token which is necessary for masked language modeling. "
                "You should pass `mlm=False` to train on causal language modeling instead."
            )

    def __call__(
        self, examples: List[Union[List[int], torch.Tensor, Dict[str, torch.Tensor]]],
    ) -> Dict[str, torch.Tensor]:
        # Handle dict or lists with proper padding and conversion to tensor.
        if isinstance(examples[0], (dict, BatchEncoding)):
            batch = pad(
                examples,
                return_tensors="pt",
                pad_to_multiple_of=self.pad_to_multiple_of,
            )
        else:
            batch = {
                "input_ids": _collate_batch(
                    examples, self.tokenizer, pad_to_multiple_of=self.pad_to_multiple_of
                )
            }

        # If special token mask has been preprocessed, pop it from the dict.
        special_tokens_mask = batch.pop("special_tokens_mask", None)
        if self.mlm:
            batch["input_ids"], batch["labels"] = self.mask_tokens(
                batch["input_ids"], special_tokens_mask=special_tokens_mask
            )
        # else:
        #     labels = batch["input_ids"].clone()
        #     if self.tokenizer.pad_token_id is not None:
        #         labels[labels == self.tokenizer.pad_token_id] = -100
        #     batch["labels"] = labels
        return batch

    def mask_tokens(
        self, inputs: torch.Tensor, special_tokens_mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Prepare masked tokens inputs/labels for masked language modeling: 80% MASK, 10% random, 10% original.
        """
        labels = inputs.clone()
        # We sample a few tokens in each sequence for MLM training (with probability `self.mlm_probability`)
        probability_matrix = torch.full(labels.shape, self.mlm_probability)
        if special_tokens_mask is None:
            special_tokens_mask = [
                self.tokenizer.get_special_tokens_mask(
                    val, already_has_special_tokens=True
                )
                for val in labels.tolist()
            ]
            special_tokens_mask = torch.tensor(special_tokens_mask, dtype=torch.bool)
        else:
            special_tokens_mask = special_tokens_mask.bool()

        probability_matrix.masked_fill_(special_tokens_mask, value=0.0)
        masked_indices = torch.bernoulli(probability_matrix).bool()
        labels[~masked_indices] = -100  # We only compute loss on masked tokens

        # 80% of the time, we replace masked input tokens with tokenizer.mask_token ([MASK])
        indices_replaced = (
            torch.bernoulli(torch.full(labels.shape, 0.8)).bool() & masked_indices
        )
        # inputs[indices_replaced] = self.tokenizer.convert_tokens_to_ids(
        #     self.tokenizer.mask_token
        # )
        inputs[indices_replaced] = self.tokenizer.token_to_id("[MASK]")

        # 10% of the time, we replace masked input tokens with random word
        indices_random = (
            torch.bernoulli(torch.full(labels.shape, 0.5)).bool()
            & masked_indices
            & ~indices_replaced
        )
        random_words = torch.randint(
            self.tokenizer.get_vocab_size(), labels.shape, dtype=torch.long
        )
        inputs[indices_random] = random_words[indices_random]

        # The rest of the time (10% of the time) we keep the masked input tokens unchanged
        return inputs, labels


def pad(
    self,
    encoded_inputs: Union[
        BatchEncoding,
        List[BatchEncoding],
        Dict[str, EncodedInput],
        Dict[str, List[EncodedInput]],
        List[Dict[str, EncodedInput]],
    ],
    padding=True,
    max_length: Optional[int] = None,
    pad_to_multiple_of: Optional[int] = None,
    return_attention_mask: Optional[bool] = None,
    return_tensors=None,
    verbose: bool = True,
) -> BatchEncoding:
    """
    Pad a single encoded input or a batch of encoded inputs up to predefined length or to the max sequence length
    in the batch.
    Padding side (left/right) padding token ids are defined at the tokenizer level (with ``self.padding_side``,
    ``self.pad_token_id`` and ``self.pad_token_type_id``)
    .. note::
        If the ``encoded_inputs`` passed are dictionary of numpy arrays, PyTorch tensors or TensorFlow tensors, the
        result will use the same type unless you provide a different tensor type with ``return_tensors``. In the
        case of PyTorch tensors, you will lose the specific device of your tensors however.
    Args:
        encoded_inputs (:class:`~transformers.BatchEncoding`, list of :class:`~transformers.BatchEncoding`, :obj:`Dict[str, List[int]]`, :obj:`Dict[str, List[List[int]]` or :obj:`List[Dict[str, List[int]]]`):
            Tokenized inputs. Can represent one input (:class:`~transformers.BatchEncoding` or :obj:`Dict[str,
            List[int]]`) or a batch of tokenized inputs (list of :class:`~transformers.BatchEncoding`, `Dict[str,
            List[List[int]]]` or `List[Dict[str, List[int]]]`) so you can use this method during preprocessing as
            well as in a PyTorch Dataloader collate function.
            Instead of :obj:`List[int]` you can have tensors (numpy arrays, PyTorch tensors or TensorFlow tensors),
            see the note above for the return type.
        padding (:obj:`bool`, :obj:`str` or :class:`~transformers.file_utils.PaddingStrategy`, `optional`, defaults to :obj:`True`):
                Select a strategy to pad the returned sequences (according to the model's padding side and padding
                index) among:
            * :obj:`True` or :obj:`'longest'`: Pad to the longest sequence in the batch (or no padding if only a
                single sequence if provided).
            * :obj:`'max_length'`: Pad to a maximum length specified with the argument :obj:`max_length` or to the
                maximum acceptable input length for the model if that argument is not provided.
            * :obj:`False` or :obj:`'do_not_pad'` (default): No padding (i.e., can output a batch with sequences of
                different lengths).
        max_length (:obj:`int`, `optional`):
            Maximum length of the returned list and optionally padding length (see above).
        pad_to_multiple_of (:obj:`int`, `optional`):
            If set will pad the sequence to a multiple of the provided value.
            This is especially useful to enable the use of Tensor Cores on NVIDIA hardware with compute capability
            >= 7.5 (Volta).
        return_attention_mask (:obj:`bool`, `optional`):
            Whether to return the attention mask. If left to the default, will return the attention mask according
            to the specific tokenizer's default, defined by the :obj:`return_outputs` attribute.
            `What are attention masks? <../glossary.html#attention-mask>`__
        return_tensors (:obj:`str` or :class:`~transformers.file_utils.TensorType`, `optional`):
            If set, will return tensors instead of list of python integers. Acceptable values are:
            * :obj:`'tf'`: Return TensorFlow :obj:`tf.constant` objects.
            * :obj:`'pt'`: Return PyTorch :obj:`torch.Tensor` objects.
            * :obj:`'np'`: Return Numpy :obj:`np.ndarray` objects.
        verbose (:obj:`bool`, `optional`, defaults to :obj:`True`):
            Whether or not to print more information and warnings.
    """
    # If we have a list of dicts, let's convert it in a dict of lists
    # We do this to allow using this method as a collate_fn function in PyTorch Dataloader
    if isinstance(encoded_inputs, (list, tuple)) and isinstance(
        encoded_inputs[0], (dict, BatchEncoding)
    ):
        encoded_inputs = {
            key: [example[key] for example in encoded_inputs]
            for key in encoded_inputs[0].keys()
        }

    # The model's main input name, usually `input_ids`, has be passed for padding
    # if self.model_input_names[0] not in encoded_inputs:
    #     raise ValueError(
    #         "You should supply an encoding or a list of encodings to this method "
    #         f"that includes {self.model_input_names[0]}, but you provided {list(encoded_inputs.keys())}"
    #     )

    required_input = encoded_inputs["input_ids"]

    if not required_input:
        if return_attention_mask:
            encoded_inputs["attention_mask"] = []
        return encoded_inputs

    # If we have PyTorch/TF/NumPy tensors/arrays as inputs, we cast them as python objects
    # and rebuild them afterwards if no return_tensors is specified
    # Note that we lose the specific device the tensor may be on for PyTorch

    first_element = required_input[0]
    if isinstance(first_element, (list, tuple)):
        # first_element might be an empty list/tuple in some edge cases so we grab the first non empty element.
        index = 0
        while len(required_input[index]) == 0:
            index += 1
        if index < len(required_input):
            first_element = required_input[index][0]
    # At this state, if `first_element` is still a list/tuple, it's an empty one so there is nothing to do.
    if not isinstance(first_element, (int, list, tuple)):
        if isinstance(first_element, torch.Tensor):
            return_tensors = "pt" if return_tensors is None else return_tensors
        elif isinstance(first_element, np.ndarray):
            return_tensors = "np" if return_tensors is None else return_tensors
        else:
            raise ValueError(
                f"type of {first_element} unknown: {type(first_element)}. "
                f"Should be one of a python, numpy, pytorch or tensorflow object."
            )

        for key, value in encoded_inputs.items():
            encoded_inputs[key] = to_py_obj(value)

    # # Convert padding_strategy in PaddingStrategy
    # padding_strategy, _, max_length, _ = self._get_padding_truncation_strategies(
    #     padding=padding, max_length=max_length, verbose=verbose
    # )

    required_input = encoded_inputs["input_ids"]
    if required_input and not isinstance(required_input[0], (list, tuple)):
        # encoded_inputs = _pad(
        #     encoded_inputs,
        #     max_length=max_length,
        #     # padding_strategy=padding_strategy,
        #     pad_to_multiple_of=pad_to_multiple_of,
        #     return_attention_mask=return_attention_mask,
        # )
        return BatchEncoding(encoded_inputs, tensor_type=return_tensors)

    batch_size = len(required_input)
    assert all(
        len(v) == batch_size for v in encoded_inputs.values()
    ), "Some items in the output dictionary have a different batch size than others."

    # if padding_strategy == PaddingStrategy.LONGEST:
    #     max_length = max(len(inputs) for inputs in required_input)
    #     padding_strategy = PaddingStrategy.MAX_LENGTH

    batch_outputs = {}
    for i in range(batch_size):
        inputs = dict((k, v[i]) for k, v in encoded_inputs.items())
        # outputs = self._pad(
        #     inputs,
        #     max_length=max_length,
        #     # padding_strategy=padding_strategy,
        #     pad_to_multiple_of=pad_to_multiple_of,
        #     return_attention_mask=return_attention_mask,
        # )
        for key, value in inputs.items():
            if key not in batch_outputs:
                batch_outputs[key] = []
            batch_outputs[key].append(value)

    return BatchEncoding(batch_outputs, tensor_type=return_tensors)


# def _pad(
#     self,
#     encoded_inputs: Union[Dict[str, EncodedInput], BatchEncoding],
#     max_length: Optional[int] = None,
#     padding_strategy: PaddingStrategy = PaddingStrategy.DO_NOT_PAD,
#     pad_to_multiple_of: Optional[int] = None,
#     return_attention_mask: Optional[bool] = None,
# ) -> dict:
#     """
#         Pad encoded inputs (on left/right and up to predefined length or max length in the batch)
#         Args:
#             encoded_inputs: Dictionary of tokenized inputs (`List[int]`) or batch of tokenized inputs (`List[List[int]]`).
#             max_length: maximum length of the returned list and optionally padding length (see below).
#                 Will truncate by taking into account the special tokens.
#             padding_strategy: PaddingStrategy to use for padding.
#                 - PaddingStrategy.LONGEST Pad to the longest sequence in the batch
#                 - PaddingStrategy.MAX_LENGTH: Pad to the max length (default)
#                 - PaddingStrategy.DO_NOT_PAD: Do not pad
#                 The tokenizer padding sides are defined in self.padding_side:
#                     - 'left': pads on the left of the sequences
#                     - 'right': pads on the right of the sequences
#             pad_to_multiple_of: (optional) Integer if set will pad the sequence to a multiple of the provided value.
#                 This is especially useful to enable the use of Tensor Core on NVIDIA hardware with compute capability
#                 >= 7.5 (Volta).
#             return_attention_mask: (optional) Set to False to avoid returning attention mask (default: set to model specifics)
#         """
#     # Load from model defaults
#     if return_attention_mask is None:
#         return_attention_mask = "attention_mask" in self.model_input_names

#     required_input = encoded_inputs[self.model_input_names[0]]

#     if padding_strategy == PaddingStrategy.LONGEST:
#         max_length = len(required_input)

#     if (
#         max_length is not None
#         and pad_to_multiple_of is not None
#         and (max_length % pad_to_multiple_of != 0)
#     ):
#         max_length = ((max_length // pad_to_multiple_of) + 1) * pad_to_multiple_of

#     needs_to_be_padded = (
#         padding_strategy != PaddingStrategy.DO_NOT_PAD
#         and len(required_input) != max_length
#     )

#     if needs_to_be_padded:
#         difference = max_length - len(required_input)
#         if self.padding_side == "right":
#             if return_attention_mask:
#                 encoded_inputs["attention_mask"] = [1] * len(required_input) + [
#                     0
#                 ] * difference
#             if "token_type_ids" in encoded_inputs:
#                 encoded_inputs["token_type_ids"] = (
#                     encoded_inputs["token_type_ids"]
#                     + [self.pad_token_type_id] * difference
#                 )
#             if "special_tokens_mask" in encoded_inputs:
#                 encoded_inputs["special_tokens_mask"] = (
#                     encoded_inputs["special_tokens_mask"] + [1] * difference
#                 )
#             encoded_inputs[self.model_input_names[0]] = (
#                 required_input + [self.pad_token_id] * difference
#             )
#         elif self.padding_side == "left":
#             if return_attention_mask:
#                 encoded_inputs["attention_mask"] = [0] * difference + [1] * len(
#                     required_input
#                 )
#             if "token_type_ids" in encoded_inputs:
#                 encoded_inputs["token_type_ids"] = [
#                     self.pad_token_type_id
#                 ] * difference + encoded_inputs["token_type_ids"]
#             if "special_tokens_mask" in encoded_inputs:
#                 encoded_inputs["special_tokens_mask"] = [
#                     1
#                 ] * difference + encoded_inputs["special_tokens_mask"]
#             encoded_inputs[self.model_input_names[0]] = [
#                 self.pad_token_id
#             ] * difference + required_input
#         else:
#             raise ValueError("Invalid padding strategy:" + str(self.padding_side))
#     elif return_attention_mask and "attention_mask" not in encoded_inputs:
#         encoded_inputs["attention_mask"] = [1] * len(required_input)

#     return encoded_inputs


def _collate_batch(examples, tokenizer, pad_to_multiple_of: Optional[int] = None):
    """Collate `examples` into a batch, using the information in `tokenizer` for padding if necessary."""
    # Tensorize if necessary.
    if isinstance(examples[0], (list, tuple)):
        examples = [torch.tensor(e, dtype=torch.long) for e in examples]

    # Check if padding is necessary.
    length_of_first = examples[0].size(0)
    are_tensors_same_length = all(x.size(0) == length_of_first for x in examples)
    if are_tensors_same_length and (
        pad_to_multiple_of is None or length_of_first % pad_to_multiple_of == 0
    ):
        return torch.stack(examples, dim=0)

    # If yes, check if we have a `pad_token`.
    if tokenizer._pad_token is None:
        raise ValueError(
            "You are attempting to pad samples but the tokenizer you are using"
            f" ({tokenizer.__class__.__name__}) does not have a pad token."
        )

    # Creating the full tensor and filling it with our data.
    max_length = max(x.size(0) for x in examples)
    if pad_to_multiple_of is not None and (max_length % pad_to_multiple_of != 0):
        max_length = ((max_length // pad_to_multiple_of) + 1) * pad_to_multiple_of
    result = examples[0].new_full([len(examples), max_length], tokenizer.pad_token_id)
    for i, example in enumerate(examples):
        if tokenizer.padding_side == "right":
            result[i, : example.shape[0]] = example
        else:
            result[i, -example.shape[0] :] = example
    return result


def to_py_obj(obj):
    if isinstance(obj, torch.Tensor):
        return obj.detach().cpu().tolist()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj
