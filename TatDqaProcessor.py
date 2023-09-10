import os
import json
from PIL import Image
from BaseProcessor import BaseProcessor


class TatDqaProcessor(BaseProcessor):
    def __init__(self, process_num: int = 512):
        self.process_num = process_num
        Image.MAX_IMAGE_PIXELS = None
        self.dataset_name = "TatDqa"
        self.jsons_dir = os.path.join(self.dataset_name, 'jsons')
        self.images_dir = os.path.join(self.dataset_name, 'images')
        self.index_dir = os.path.join(self.dataset_name)
        if not os.path.exists(self.jsons_dir):
            os.mkdir(self.jsons_dir)

        if not os.path.exists(self.images_dir):
            os.mkdir(self.images_dir)

    def combine_jsons_into_jsonl(self, indir, outdir):
        # combine all jsons into one jsonl file
        all_files = os.listdir(indir)
        cnt = 0
        with open(os.path.join(outdir, 'documents_content.jsonl'), 'w') as outfile:
            for file in all_files:
                if not file.endswith('.json'):
                    continue
                with open(os.path.join(indir, file), 'r', encoding='utf-8') as infile:
                    backup = infile
                    obj = json.load(infile)
                    if len(obj["pages"]) > 1:
                        continue
                    infile = backup
                    lines = infile.readlines()
                    for line in lines:
                        outfile.write(line[:-1].strip())
                outfile.write('\n')
