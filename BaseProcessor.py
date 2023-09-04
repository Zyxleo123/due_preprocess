import os
import json
from copy import deepcopy

from tqdm import tqdm
from pdf2image import convert_from_path


class BaseProcessor:
    def __init__(self, dataset_folder_name: str):
        if not os.path.exists(dataset_folder_name):
            raise FileNotFoundError(f"The folder '{dataset_folder_name}' not found in current working directory.")

        self.dataset_name = dataset_folder_name
        self.jsons_dir = os.path.join(self.dataset_name, 'jsons')
        self.images_dir = os.path.join(self.dataset_name, 'images')
        self.pdf_dir = os.path.join(self.dataset_name, 'pdf')
        self.index_dir = os.path.join(self.dataset_name)

        if not os.path.exists(self.jsons_dir):
            os.mkdir(self.jsons_dir)

        if not os.path.exists(self.images_dir):
            os.mkdir(self.images_dir)

    @staticmethod
    def get_box(position):
        x1, y1, x2, y2 = position[:]
        return [[x1, y2], [x2, y2], [x2, y1], [x1, y1]]

    def save_image(self, pdf_name):
        file_path = os.path.join(self.pdf_dir, f'{pdf_name}.pdf')
        img = convert_from_path(file_path)[0]
        width, height = img.size
        fname = f'{pdf_name}.png'
        img.save(os.path.join(self.images_dir, fname))
        return {"width": width, "height": height, "fname": fname}

    def write_json(self, processed_record):
        file_name = processed_record["id"]
        with open(os.path.join(self.jsons_dir, f'{file_name}.json'), 'w') as json_file:
            json.dump(processed_record, json_file)

    def clear_index_files(self):
        splits = ('train', 'dev', 'test', 'all')
        index_files_path = [os.path.join(self.index_dir, f"{self.dataset_name}.{split}.txt") for split in splits]
        for path in index_files_path:
            with open(path, 'w'):
                pass

    def write_index_file(self, image_file_name, json_file_name, split_name):
        image_file_name += '.png'
        json_file_name += '.json'
        index_file_path1 = os.path.join(self.index_dir, self.dataset_name + '.' + split_name + '.txt')
        index_file_path2 = os.path.join(self.index_dir, self.dataset_name + '.' + 'all' + '.txt')
        with open(index_file_path1, 'a') as index_file1, open(index_file_path2, 'a') as index_file2:
            index_file1.write(
                f"{os.path.join(self.dataset_name, 'images', image_file_name)}\t"
                f"{os.path.join(self.dataset_name, 'jsons', json_file_name)}\n")
            index_file2.write(
                f"{os.path.join(self.dataset_name, 'images', image_file_name)}"
                f"\t{os.path.join(self.dataset_name, 'jsons', json_file_name)}\n")

    def add_query(self, *args, **kwargs):
        raise NotImplementedError("Abstravt method add_query not implemented")

    def add_ocr(self, *args, **kwargs):
        raise NotImplementedError("Abstract method add_ocr not implemented")

    def process_line(self, split, line1, line2):
        record_query = json.loads(line1)
        record_ocr = json.loads(line2)
        pdf_name = record_ocr["name"]
        split_name = record_query["split"]
        full_id = self.dataset_name + '_' + split + '_' + pdf_name
        record_init = {"id": full_id,
                       "input": {"id": full_id, "uid": full_id,
                                 "img": self.save_image(pdf_name)}}
        query_num = len(record_query['annotations'])
        ocr_num = len(record_ocr["contents"])
        for ocr_id in range(ocr_num):
            record_with_doc = deepcopy(record_init)
            record_with_doc = self.add_ocr(record_with_doc, record_ocr["contents"][ocr_id])
            for query_id in range(query_num):
                record_final = deepcopy(record_with_doc)
                record_final = self.add_query(record_final, record_query['annotations'][query_id])
                self.write_json(record_final)
                self.write_index_file(pdf_name, record_final["id"], split_name)

    def process_jsonl(self, split='', num_lines=None):
        file1_path = os.path.join(self.dataset_name, split, 'document.jsonl')
        file2_path = os.path.join(self.dataset_name, split, 'documents_content.jsonl')

        with open(file1_path, 'r', encoding="utf-8") as file1, open(file2_path, 'r', encoding="utf-8") as file2:
            file_line_num = len(file1.readlines()) if num_lines is None else num_lines
            bar = tqdm(enumerate(zip(file1, file2)), total=file_line_num, leave=False)
            for i, (line1, line2) in bar:
                if i == num_lines:
                    break
                self.process_line(split, line1, line2)

    def process_dataset(self, num_lines=None):
        self.clear_index_files()
        if not os.path.exists(self.dataset_name):
            raise FileNotFoundError(f"Dataset '{self.dataset_name}' not found."
                                    f"Please create an empty directory and add necessary pdfs")
        if not os.path.exists(os.path.join(self.dataset_name, 'jsons')):
            os.mkdir(os.path.join(self.dataset_name, 'jsons'))
        if not os.path.exists(os.path.join(self.dataset_name, 'images')):
            os.mkdir(os.path.join(self.dataset_name, 'images'))

        splits = ('train', 'dev', 'test')
        bar = tqdm(enumerate(splits), total=len(splits), leave=False)
        bar.set_description(f"Processing {os.path.join(self.dataset_name)}...")
        for i, split in bar:
            bar.set_postfix({"Split": split})
            self.process_jsonl(split, num_lines)
