# inheritit from baseprocessor
from VQA_WikiProcessor import VQA_WikiProcessor
from BaseProcessor import BaseProcessor


class TabFactProcessor(VQA_WikiProcessor):
    def __init__(self, dataset_folder_name):
        if dataset_folder_name != "TabFact":
            raise ValueError(f"{dataset_folder_name} does not match this processor."
                             f" Please choose TabFact(case sensitive)")

        BaseProcessor.__init__(self, dataset_folder_name)

    dataset_ocr2tokens_layer_name = {"tab_te": "common_format", "tab_mi": "common_format", "tab_dj": "tokens_layer"}





