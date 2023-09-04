# Check if every json line of the document.jsonl under kleister-charitya & Deepform directory has a property that
# every dict of json_obj["annotations"] has a values field that has a length of 1.
import json

with open("kleister-charity/document.jsonl", "r") as f1, open("DeepForm/document.jsonl", "r") as f2:
    for f in (f1, f2):
        for line in f.readlines():
            json_obj = json.loads(line)
            for annotation in json_obj["annotations"]:
                if len(annotation["values"]) != 1:
                    print(json_obj["name"])
        print(f"file: {f.name} Done")

# Further check every split(might not be necessary)
for split in ["train", "dev", "test"]:
    with open(f"kleister-charity/{split}/document.jsonl", "r", encoding="utf-8") as f1, \
            open(f"DeepForm/{split}/document.jsonl", "r", encoding="utf-8") as f2:
        for f in (f1, f2):
            for line in f.readlines():
                json_obj = json.loads(line)
                for annotation in json_obj["annotations"]:
                    if len(annotation["values"]) != 1:
                        print(json_obj["name"])
            print(f"file: {f.name} split: {split} Done")
