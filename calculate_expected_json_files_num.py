# Calculate the expected number of json files generated from a (document.jsonl, documents_content.jsonl) pair.
# The expected number is calculated this way:
# 1. We read in one line of each jsonl file at a time.
# We assume that the number of lines in document.jsonl is equal to the number of lines in documents_content.jsonl.
# We ignore any line in documents_content.jsonl that has multiple pages.
# We check this by getting the length of obj["contents"][0]["tokens_layer"]["structures"]["pages"]["positions"].
# If the length is greater than 1, we ignore this line.
# 2. We calculate the number of queries in the current line of document.jsonl.
# We get the length of obj["annotations"].
import json
import os
from tqdm import tqdm


def cal_all(dataset_name, split_name, tot=None):
    file1_path = os.path.join(dataset_name, split_name, 'document.jsonl')
    file2_path = os.path.join(dataset_name, split_name, 'documents_content.jsonl')
    num_lines = 0
    cnt = 0
    with open(file1_path, 'r', encoding="utf-8") as file1, open(file2_path, 'r', encoding="utf-8") as file2:
        file1, file2 = file1.readlines(), file2.readlines()
        line_num = len(file1)
        bar = tqdm(zip(file1, file2), total=line_num, leave=False)
        for line1, line2 in bar:
            if tot is not None and cnt == tot:
                break
            obj1 = json.loads(line1)
            obj2 = json.loads(line2)
            if len(obj2["contents"][0]["tokens_layer"]["structures"]["pages"]["positions"]) > 1:
                cnt += 1
                continue
            num_lines += len(obj1["annotations"])
            cnt += 1
    print(cnt, "lines processed")
    return num_lines


def cal_multi(dataset_name, split_name, tot=None):
    file1_path = os.path.join(dataset_name, split_name, 'document.jsonl')
    file2_path = os.path.join(dataset_name, split_name, 'documents_content.jsonl')
    num_lines = 0
    cnt = 0
    with open(file1_path, 'r', encoding="utf-8") as file1, open(file2_path, 'r', encoding="utf-8") as file2:
        file1, file2 = file1.readlines(), file2.readlines()
        line_num = len(file1)
        bar = tqdm(zip(file1, file2), total=line_num, leave=False)
        for line1, line2 in bar:
            if tot is not None and cnt == tot:
                break
            obj1 = json.loads(line1)
            obj2 = json.loads(line2)
            if len(obj2["contents"][0]["tokens_layer"]["structures"]["pages"]["positions"]) <= 1:
                cnt += 1
                continue
            num_lines += len(obj1["annotations"])
            cnt += 1
    print(cnt, "lines processed")
    return num_lines


def cal_single(dataset_name, split_name, tot=None):
    file1_path = os.path.join(dataset_name, split_name, 'document.jsonl')
    file2_path = os.path.join(dataset_name, split_name, 'documents_content.jsonl')
    num_lines = 0
    cnt = 0
    with open(file1_path, 'r', encoding="utf-8") as file1, open(file2_path, 'r', encoding="utf-8") as file2:
        file1, file2 = file1.readlines(), file2.readlines()
        line_num = len(file1)
        bar = tqdm(zip(file1, file2), total=line_num, leave=False)
        for line1, line2 in bar:
            if tot is not None and cnt == tot:
                cnt += 1
                break
            obj1 = json.loads(line1)
            obj2 = json.loads(line2)
            num_lines += len(obj1["annotations"])
            cnt += 1
    print(cnt, "lines processed")
    return num_lines


if __name__ == "__main__":
    dataset_names = ("docvqa", "infographics_vqa", "WikiTableQuestions", "TabFact")
    split_names = ("train", "dev", "test", "")
    input_dataset_idx = int(input("输入数据集编号(vqa, infovqa, wtq, tabfact): "))
    input_split_idx = int(input("输入数据集分割编号(train, dev, test, all): "))
    tot = int(input("输入要计算的文件数目(默认为全部): ") or -1)
    dataset_name = dataset_names[input_dataset_idx - 1]
    split_name = split_names[input_split_idx - 1]
    print("single:", cal_single(dataset_name, split_name, tot), "\nmulti:", cal_multi(dataset_name, split_name, tot),
          "\nall: ", cal_all(dataset_name, split_name, tot))
