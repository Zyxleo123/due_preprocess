import json
import os
from copy import deepcopy

from pdf2image import convert_from_path

ROOT = os.getcwd()
PDFS_PATH = os.path.join(ROOT, 'pdfs')
JSONS_PATH = os.path.join(ROOT, 'JSONS')
IMAGES_PATH = os.path.join(ROOT,  'IMAGES')
DATASET_BASE = os.path.join(ROOT, 'DUE')
INDEX_PATH = ROOT


def save_image(pdf_name):
    file_path = os.path.join(PDFS_PATH, f'{pdf_name}.pdf')
    img = convert_from_path(file_path)[0]
    width, height = img.size
    fname = f'{pdf_name}.png'
    img.save(os.path.join(IMAGES_PATH, fname))
    return {"width": width, "height": height, "fname": fname}


def get_box(position):
    x1, y1, x2, y2 = position[:]
    return [[x1, y2], [x2, y2], [x2, y1], [x1, y1]]


def add_query(record_with_query, query):
    question_id = str(query["metadata"]["question_id"])
    record_with_query["id"] += '_' + question_id
    record_with_query["input"]["id"] += '_' + question_id
    record_with_query["input"]["uid"] += '_' + question_id
    record_with_query["query"] = query["key"]
    record_with_query["instruction"] = query["key"]
    record_with_query["output"] = []
    for value in query["values"]:
        record_with_query["output"].extend(value["value_variants"])
    return record_with_query


def add_ocr(record_with_doc, content):
    tool_name = content["tool_name"]
    if tool_name == "tesseract":
        tokens_layer = content["tokens_layer"]
    elif tool_name == "microsoft_cv":
        tokens_layer = content["common_format"]
    else:
        raise ValueError("不支持的OCR格式")
    record_with_doc["id"] += '_' + tool_name[0:2]
    record_with_doc["input"]["id"] += '_' + tool_name[0:2]
    record_with_doc["input"]["uid"] += '_' + tool_name[0:2]

    tokens = tokens_layer["tokens"]
    token_positions = tokens_layer["positions"]
    lines = tokens_layer["structures"]["lines"]
    structure_value = lines["structure_value"]
    seg_positions = lines["positions"]
    line_num = len(lines["structure_value"])

    document = []
    for line_idx in range(line_num):
        cur_line_dict = {"id": line_idx, "box": get_box(seg_positions[line_idx])}

        line_start_idx = structure_value[line_idx][0]
        line_end_idx = structure_value[line_idx][1]
        cur_line_dict["text"] = " ".join(tokens[line_start_idx:line_end_idx])

        cur_line_dict_words = []
        for token_idx in range(line_start_idx, line_end_idx):
            cur_line_dict_words_dict = {"id": token_idx,
                                        "box": get_box(token_positions[token_idx]),
                                        "text": tokens[token_idx]}
            cur_line_dict_words.append(cur_line_dict_words_dict)

        cur_line_dict["words"] = cur_line_dict_words
        document.append(cur_line_dict)

    record_with_doc["input"]["document"] = document
    return record_with_doc


def process_vqa_line(dataset_name, split, line1, line2):
    record_query = json.loads(line1)
    record_ocr = json.loads(line2)
    pdf_name = record_ocr["name"]
    split_name = record_query["split"]
    full_id = dataset_name + '_' + split + '_' + pdf_name
    record_init = {"id": full_id,
                   "input": {"id": full_id, "uid": full_id,
                             "image": save_image(pdf_name)}}
    query_num = len(record_query['annotations'])
    ocr_num = len(record_ocr["contents"])
    for ocr_id in range(ocr_num):
        record_with_doc = deepcopy(record_init)
        record_with_doc = add_ocr(record_with_doc, record_ocr["contents"][ocr_id])
        for query_id in range(query_num):
            record_final = deepcopy(record_with_doc)
            record_final = add_query(record_final, record_query['annotations'][query_id])
            write_json(record_final)
            write_index_file(dataset_name, pdf_name, record_final["id"], split_name)


def process_vqa_jsonl(dataset_name, split='', line_num=None):
    file1_path = os.path.join(DATASET_BASE, dataset_name, split, 'document.jsonl')
    file2_path = os.path.join(DATASET_BASE, dataset_name, split, 'documents_content.jsonl')

    with open(file1_path, 'r', encoding="utf-8") as file1, open(file2_path, 'r', encoding="utf-8") as file2:
        for i, (line1, line2) in enumerate(zip(file1, file2)):
            if i == line_num:
                break
            process_vqa_line(dataset_name, split, line1, line2)


def write_json(processed_record):
    file_name = processed_record["id"]
    with open(os.path.join(JSONS_PATH, file_name), 'w') as json_file:
        json.dump(processed_record, json_file, indent=4)


def write_index_file(dataset_name, image_file_name, json_file_name, split_name):
    image_file_name += '.png'
    json_file_name += '.json'
    index_file_name1 = dataset_name + '.' + split_name + '.txt'
    index_file_name2 = dataset_name + '.' + 'all' + '.txt'
    with open(index_file_name1, 'a') as index_file1, open(index_file_name2, 'a') as index_file2:
        index_file1.write(image_file_name + '\t' + json_file_name + '\n')
        index_file2.write(image_file_name + '\t' + json_file_name + '\n')


if __name__ == '__main__':
    process_vqa_jsonl('test_data', 'test_split')