## JSON文件命名
    test_data_test_split_kmwn0226_18_mi_41686 = 数据集名+split名+pdf名+OCR名缩略+query编号
## PDF文件
    目前需要把所有数据集的PDF文件统一放到同一个目录下
## 数据集
    一个数据集以 数据集名为一级目录（类似docvqa)/split名为二级目录（类似train）/两个jsonl文件放置其下(document.jsonl/documents_content.jsonl)
    如果需要在上述一级目录之上再添加一级，需要在源文件中修改路径"ROOT"
## 输出文件
    一份pdf对应一份png；一行jsonl对应（query_num * OCR_num)个json文件
## 主函数使用说明
    第一个参数为一级目录下的一个数据集名，第二个参数为其中的一个split名，默认值为空，代表"all"；第三个参数用于测试，指定处理多少行
    例如process_vqa_jsonl('test_data', 'test_split')处理./test_data/test_split下的2个jsonl文件，它们的内容来自2个数据集(vqa, infovqa)，其中一个是钉钉上的示例输出。

