from BaseProcessor import BaseProcessor


class VQA_WikiProcessor(BaseProcessor):
    def __init__(self, dataset_folder_name):
        if dataset_folder_name not in ("docvqa", "WikiTableQuestions", "infographics_vqa"):
            raise ValueError(f"{dataset_folder_name} does not match this processor."
                             f" Please choose between docvqa, WikiTableQuestions or infographics_vqa(case sensitive)")

        super().__init__(dataset_folder_name)

    def add_query(self, record_with_query, query):
        question_id = str(query["metadata"]["question_id"])
        record_with_query["id"] += '_' + question_id
        record_with_query["input"]["id"] += '_' + question_id
        record_with_query["input"]["uid"] += '_' + question_id
        record_with_query["query"] = query["key"]
        record_with_query["instruction"] = query["key"]
        record_with_query["output"] = []
        for value_dict in query["values"]:
            if "value_variants" in value_dict:
                record_with_query["output"].extend(value_dict["value_variants"])
            else:
                record_with_query["output"].append(value_dict["value"])
        return record_with_query

    dataset_ocr2tokens_layer_name = {"doc_te": "tokens_layer", "doc_mi": "common_format",
                                     "inf_te": "tokens_layer", "inf_mi": "common_format",
                                     "wik_te": "common_format", "wik_mi": "common_format", "wik_dj": "tokens_layer"}

    def add_ocr(self, record_with_doc, content):
        tool_name = content["tool_name"]
        dataset_name_and_tool_name = self.dataset_name.lower()[:3] + '_' + tool_name[:2]
        tokens_layer_name = self.dataset_ocr2tokens_layer_name.get(dataset_name_and_tool_name)

        tokens_layer = content[tokens_layer_name]
        record_with_doc["id"] += '_' + tool_name[:2]
        record_with_doc["input"]["id"] += '_' + tool_name[:2]
        record_with_doc["input"]["uid"] += '_' + tool_name[:2]

        tokens = tokens_layer["tokens"]
        token_positions = tokens_layer["positions"]
        lines = tokens_layer["structures"]["lines"]
        structure_value = lines["structure_value"]
        seg_positions = lines["positions"]
        line_num = len(lines["structure_value"])

        document = []
        for line_idx in range(line_num):
            cur_line_dict = {"id": line_idx, "box": self.get_box(seg_positions[line_idx])}

            line_start_idx = structure_value[line_idx][0]
            line_end_idx = structure_value[line_idx][1]
            cur_line_dict["text"] = " ".join(tokens[line_start_idx:line_end_idx])

            cur_line_dict_words = []
            for token_idx in range(line_start_idx, line_end_idx):
                cur_line_dict_words_dict = {"id": token_idx,
                                            "box": self.get_box(token_positions[token_idx]),
                                            "text": tokens[token_idx]}
                cur_line_dict_words.append(cur_line_dict_words_dict)

            cur_line_dict["words"] = cur_line_dict_words
            document.append(cur_line_dict)

        record_with_doc["input"]["document"] = document
        return record_with_doc


debug_set = ("docvqa", "infographics_vqa", "WikiTableQuestions")
if __name__ == "__main__":
    print("请选择调试哪些数据集:")
    debug_list = []
    for i, debug_option in enumerate(debug_set):
        print(f"{i + 1}. {debug_option}")
    choice = int(input("输入选择的数字 (1-3, 0结束输入): "))
    while choice != 0:
        debug_list.append(choice)
        choice = int(input("输入选择的数字 (1-3, 0结束输入): "))
        if choice in debug_list:
            choice = int(input("重复了。输入选择的数字 (1-3, 0结束输入): "))

    for choice in debug_list:
        test_processor = VQA_WikiProcessor(debug_set[choice - 1])
        test_processor.process_dataset(2)
