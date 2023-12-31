import os
import json
from PIL import Image
from copy import deepcopy

from tqdm import tqdm
from pdf2image import convert_from_path
from multiprocessing.pool import ThreadPool


class BaseProcessor:
    def __init__(self, dataset_folder_name: str):
        Image.MAX_IMAGE_PIXELS = None
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
    def get_box(position, ratio_w, ratio_h):
        x1, y1, x2, y2 = position[:]  # 左上右下
        x1, x2 = int(x1 * ratio_w), int(x2 * ratio_w)
        y1, y2 = int(y1 * ratio_h), int(y2 * ratio_h)
        return [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]  # 左上；右上；右下；左下

    @staticmethod
    def query_preprocess(query: str):
        raise NotImplementedError("Abstract method query_preprocess not implemented")

    def save_image(self, pdf_name):
        file_path = os.path.join(self.pdf_dir, f'{pdf_name}.pdf')
        img = convert_from_path(file_path)[0]
        width, height = img.size
        if (width > 5000) or (height > 5000):
            # equal scaling to 5000
            ratio = min(5000 / width, 5000 / height)
            width, height = int(width * ratio), int(height * ratio)
            img = img.resize((width, height), Image.Resampling.LANCZOS)

        fname = f'{pdf_name}.png'
        img.save(os.path.join(self.images_dir, fname), optimize=True, quality=50)
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
        raise NotImplementedError("Abstract method add_query not implemented")

    def add_ocr(self, *args, **kwargs):
        raise NotImplementedError("Abstract method add_ocr not implemented")

    def process_line(self, split, line1, line2):
        record_query = json.loads(line1)
        record_ocr = json.loads(line2)
        pdf_name = record_ocr["name"]
        if pdf_name in self.processed_set:
            if self.bar:
                self.bar.update(1)
            return
        split_name = record_query["split"]
        full_id = self.dataset_name + '_' + split + '_' + pdf_name
        record_init = {"id": full_id,
                       "input": {"id": full_id, "uid": full_id,
                                 "img": self.save_image(pdf_name)}}
        compressed_width = record_init["input"]["img"]["width"]
        compressed_height = record_init["input"]["img"]["height"]
        query_num = len(record_query['annotations'])
        # Choose microsoft_ocr over any other. If not found, choose tesseract.
        ocr_num = len(record_ocr["contents"])
        ocr_id, flag = 0, False
        for ocr_id in range(ocr_num):
            if record_ocr["contents"][ocr_id]["tool_name"] == "microsoft_cv":
                flag = True
                break
        if not flag:
            for ocr_id in range(ocr_num):
                if record_ocr["contents"][ocr_id]["tool_name"] == "tesseract":
                    break
        record_with_doc = record_init
        record_with_doc = self.add_ocr(record_with_doc, record_ocr["contents"][ocr_id],
                                       compressed_width, compressed_height)
        for query_id in range(query_num):
            record_final = deepcopy(record_with_doc)
            record_final = self.add_query(record_final, record_query['annotations'][query_id])
            self.write_json(record_final)
            self.write_index_file(pdf_name, record_final["id"], split_name)
        if self.bar:
            self.bar.update(1)

    def process_jsonl(self, split, num_lines):
        file1_path = os.path.join(self.dataset_name, split, 'document.jsonl')
        file2_path = os.path.join(self.dataset_name, split, 'documents_content.jsonl')

        with open(file1_path, 'r', encoding="utf-8") as file1, open(file2_path, 'r', encoding="utf-8") as file2:
            file1, file2 = file1.readlines(), file2.readlines()
            file_line_num = len(file1) if num_lines is None else num_lines
            self.bar = tqdm(total=file_line_num, leave=False)

            do_multiprocess = True
            if do_multiprocess:
                pool = ThreadPool(processes=32)
                for i, (line1, line2) in enumerate(zip(file1, file2)):
                    if i == file_line_num:
                        break
                    out = pool.apply_async(func=self.process_line, args=(split, line1, line2))
                pool.close()
                pool.join()
            else:
                for i, (line1, line2) in enumerate(zip(file1, file2)):
                    if i == file_line_num:
                        break
                    self.process_line(split, line1, line2)

            self.bar.close()

    def process_dataset(self, num_lines=None, splits=('train', 'dev', 'test')):
        # Check if every pdf file is processed
        self.complete_set = set()
        pdf_names = os.listdir(self.pdf_dir)
        for pdf_name in pdf_names:
            if pdf_name.endswith('.pdf'):
                self.complete_set.add(pdf_name[:-4])
        self.processed_set = set()
        
        self.clear_index_files()

        bar = tqdm(enumerate(splits), total=len(splits), leave=False)
        bar.set_description(f"Processing {os.path.join(self.dataset_name)}...")
        while self.processed_set != self.complete_set:
            for i, split in bar:
                bar.set_postfix({"Split": split})
                self.process_jsonl(split=split, num_lines=num_lines)
            # Report how many left by comparing two sets
            bar.set_postfix({"Left": len(self.complete_set - self.processed_set)})
            if splits != ('train', 'dev', 'test'):
                break
