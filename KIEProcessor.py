import json
from copy import deepcopy
from BaseProcessor import BaseProcessor


class KIEProcessor(BaseProcessor):
    def __init__(self, dataset_folder_name, prompt):
        if dataset_folder_name not in ("kleister-charity", "DeepForm"):
            raise ValueError(f"{dataset_folder_name} does not match this processor."
                             f" Please choose between kleister-charity, DeepForm(case sensitive)")
        self.question_id = 0
        self.prompt = prompt
        super().__init__(dataset_folder_name)

    def process_line(self, split, line1, line2):
        record_query = json.loads(line1)
        record_ocr = json.loads(line2)
        # ------------------ 以下是重载的代码 ------------------
        # kleister-charity的pdf_name是带多余的.pdf后缀的（已确认）
        pdf_name = record_ocr["name"][:-4] if self.dataset_name == "kleister-charity" else record_ocr["name"]
        # ------------------ 以上是重载的代码 ------------------
        split_name = record_query["split"]
        full_id = self.dataset_name + '_' + split + '_' + pdf_name
        record_init = {"id": full_id,
                       "input": {"id": full_id, "uid": full_id,
                                 "img": self.save_image(pdf_name)}}
        compressed_width = record_init["input"]["img"]["width"]
        compressed_height = record_init["input"]["img"]["height"]
        query_num = len(record_query['annotations'])
        ocr_num = len(record_ocr["contents"])
        for ocr_id in range(ocr_num):
            record_with_doc = deepcopy(record_init)
            record_with_doc = self.add_ocr(record_with_doc, record_ocr["contents"][ocr_id],
                                           compressed_width, compressed_height)
            for query_id in range(query_num):
                record_final = deepcopy(record_with_doc)
                record_final = self.add_query(record_final, record_query['annotations'][query_id])
                self.write_json(record_final)
                self.write_index_file(pdf_name, record_final["id"], split_name)

    def add_query(self, record_with_query, annotation):
        question_id = str(self.question_id)
        self.question_id += 1
        record_with_query["id"] += '_' + question_id
        record_with_query["input"]["id"] += '_' + question_id
        record_with_query["input"]["uid"] += '_' + question_id
        record_with_query["query"] = self.prompt + ' ' + annotation["key"]
        record_with_query["instruction"] = self.prompt + ' ' + annotation["key"]
        assert len(annotation["values"]) == 1
        record_with_query["output"] = annotation["values"][0]["value"]
        return record_with_query

    dataset_ocr2tokens_layer_name = {"dee_te": "common_format", "dee_mi": "common_format", "dee_dj": "tokens_layer",
                                     "kle_te": "tokens_layer", "kle_mi": "common_format"}

    def add_ocr(self, record_with_doc, content, compressed_width, compressed_height):
        tool_name = content["tool_name"]
        dataset_name_and_tool_name = self.dataset_name.lower()[:3] + '_' + tool_name[:2]
        tokens_layer_name = self.dataset_ocr2tokens_layer_name.get(dataset_name_and_tool_name)

        tokens_layer = content[tokens_layer_name]
        record_with_doc["id"] += '_' + tool_name[:2]
        record_with_doc["input"]["id"] += '_' + tool_name[:2]
        record_with_doc["input"]["uid"] += '_' + tool_name[:2]

        original_width = tokens_layer["structures"]["pages"]["positions"][0][2] - \
                         tokens_layer["structures"]["pages"]["positions"][0][0]
        original_height = tokens_layer["structures"]["pages"]["positions"][0][3] - \
                          tokens_layer["structures"]["pages"]["positions"][0][1]
        ratio_width = compressed_width / original_width
        ratio_height = compressed_height / original_height

        tokens = tokens_layer["tokens"]
        token_positions = tokens_layer["positions"]

        lines = tokens_layer["structures"]["lines"]
        structure_value = lines["structure_value"]
        seg_positions = lines["positions"]
        line_num = len(lines["structure_value"])

        document = []
        for line_idx in range(line_num):
            cur_line_dict = {"id": line_idx, "box": self.get_box(seg_positions[line_idx], ratio_width, ratio_height)}

            line_start_idx = structure_value[line_idx][0]
            line_end_idx = structure_value[line_idx][1]
            cur_line_dict["text"] = " ".join(tokens[line_start_idx:line_end_idx])

            cur_line_dict_words = []
            for token_idx in range(line_start_idx, line_end_idx):
                cur_line_dict_words_dict = {"id": token_idx,
                                            "box": self.get_box(token_positions[token_idx], ratio_width, ratio_height),
                                            "text": tokens[token_idx]}
                cur_line_dict_words.append(cur_line_dict_words_dict)

            cur_line_dict["words"] = cur_line_dict_words
            document.append(cur_line_dict)

        record_with_doc["input"]["document"] = document
        return record_with_doc


debug_set = ("kleister-charity", "DeepForm")
if __name__ == "__main__":
    print("请选择调试哪些数据集:")
    debug_list = []
    for i, debug_option in enumerate(debug_set):
        print(f"{i + 1}. {debug_option}")
    choice = int(input("输入选择的数字 (1-2, 0结束输入): "))
    while choice != 0:
        debug_list.append(choice)
        choice = int(input("输入选择的数字 (1-2, 0结束输入): "))
        if choice in debug_list:
            choice = int(input("重复了。输入选择的数字 (1-2, 0结束输入): "))

    prompt = input("请输入prompt(不必尾后空格): ")

    for choice in debug_list:
        test_processor = KIEProcessor(debug_set[choice - 1], prompt)
        test_processor.process_dataset(2)
