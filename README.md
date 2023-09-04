## JSON文件命名
    test_data_test_split_kmwn0226_18_mi_41686 = 数据集名+split名+pdf名+OCR名缩略+query编号
## 文件结构(v2)
    根/{源文件.py，dataset若干/{pdf, images, splits, json, 索引.txt}}
## 输出文件
    一份pdf对应一份png；一行jsonl对应（query_num * OCR_num)个json文件
## 使用说明(v3)
    建立VQA_WikiProcessor实例，参数输入dataset名（有限制）。调用process_dataset()。
    KIEProcessor类似，额外输入一个prompt(比如"What is the")
### 小批量测试
    小批量数据测试直接运行VQA_WikiProcessor.py/KIEProcessor.py 测试pdf文件已经包含在仓库里
### test.py
    运行此文件，验证每一个KIE问题只有一个答案。