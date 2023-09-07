from BaseProcessor import BaseProcessor


class VQA_Wiki_TabFactProcessor(BaseProcessor):
    def __init__(self, dataset_folder_name):
        if dataset_folder_name not in ("docvqa", "WikiTableQuestions", "infographics_vqa", "TabFact"):
            raise ValueError(f"{dataset_folder_name} does not match this processor."
                             f" Please choose between docvqa, WikiTableQuestions, infographics_vqa,"
                             f" or TabFact(case sensitive)")
        # TabFact is a special case, because it has no metadata["question_id"] in its json files.
        # So we need to add a question_id to each question.
        self.question_id = 0
        super().__init__(dataset_folder_name)

    def query_preprocess(self, query: str):
        return query

    def add_query(self, record_with_query, annotation):
        question_id = str(annotation["metadata"]["question_id"]) if self.dataset_name != "TabFact" else str(
            self.question_id)
        if self.dataset_name == "TabFact":
            self.question_id += 1
        record_with_query["id"] += '_' + question_id
        record_with_query["input"]["id"] += '_' + question_id
        record_with_query["input"]["uid"] += '_' + question_id
        record_with_query["query"] = annotation["key"]
        record_with_query["instruction"] = annotation["key"]
        record_with_query["output"] = []
        for value_dict in annotation["values"]:
            if "value_variants" in value_dict:
                record_with_query["output"].extend(value_dict["value_variants"])
            else:
                if self.dataset_name == "TabFact":
                    assert value_dict["value"] in ("0", "1")
                    record_with_query["output"] = "yes" if value_dict["value"] == "1" else "no"
                else:
                    assert self.dataset_name == "WikiTableQuestions"
                    record_with_query["output"].append(value_dict["value"])
        if isinstance(record_with_query["output"], list):
            # Get the most frequent answer as the final answer. If there are multiple answers with the same frequency,
            # choose randomly.
            record_with_query["output"] = max(set(record_with_query["output"]), key=record_with_query["output"].count)
        return record_with_query

    dataset_ocr2tokens_layer_name = {"doc_te": "tokens_layer", "doc_mi": "common_format",
                                     "inf_te": "tokens_layer", "inf_mi": "common_format",
                                     "wik_te": "common_format", "wik_mi": "common_format", "wik_dj": "tokens_layer",
                                     "tab_te": "common_format", "tab_mi": "common_format", "tab_dj": "tokens_layer"}

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


debug_set = ("docvqa", "infographics_vqa", "WikiTableQuestions", "TabFact")
if __name__ == "__main__":
    print("请选择调试哪些数据集:")
    debug_list = []
    for i, debug_option in enumerate(debug_set):
        print(f"{i + 1}. {debug_option}")
    choice = int(input("输入选择的数字 (1-4, 0结束输入): "))
    while choice != 0:
        debug_list.append(choice)
        choice = int(input("输入选择的数字 (1-4, 0结束输入): "))
        if choice in debug_list:
            choice = int(input("重复了。输入选择的数字 (1-4, 0结束输入): "))

    for choice in debug_list:
        test_processor = VQA_Wiki_TabFactProcessor(debug_set[choice - 1])
        test_processor.process_dataset(2)
