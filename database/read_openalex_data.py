import os
import gzip
import json
import time
from datetime import datetime
from zoneinfo import ZoneInfo

def get_foldernames(path: str) -> list[str]:
    return [
        f for f in os.listdir(path) 
        if os.path.isdir(os.path.join(path, f))
    ]

def get_filenames(path: str) -> list[str]:
    return [
        f for f in os.listdir(path)
        if os.path.isfile(os.path.join(path, f))
    ]


def parse_abstract(inverted_index: dict) -> str:
    if not inverted_index:
        return ""
    
    # Find the total length
    max_pos = max(pos for positions in inverted_index.values() for pos in positions)
    
    # Place each word at its position(s)
    words = [""] * (max_pos + 1)
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word
    
    return " ".join(words)

def append_to_json(filepath, new_entry):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    data.append(new_entry)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

start_time = time.time()
start = datetime.fromtimestamp(start_time, tz=ZoneInfo("Europe/Berlin"))
print(start)

openalex_works_folder = 'D:\\openalex-snapshot\\data\\works'
update_folders = get_foldernames(openalex_works_folder)
language_en = 'en'
language_de = 'de'
search_type = 'article'
search_title_en = 'vector database'
search_title_de = 'vektordatenbank'

'''
### loop version with language
for update_folder in update_folders:
    gz_files = get_filenames(f'{openalex_works_folder}\\{update_folder}')
    for gz_file in gz_files:
        with gzip.open(f'{openalex_works_folder}\\{update_folder}\\{gz_file}', 'rt', encoding='utf-8') as lines:
            for line in lines:
                    work = json.loads(line)
                    work_type = work.get('type') or ''
                    if search_type in work_type.lower():
                        work_language = work.get('language') or ''
                        if language_en in work_language.lower() or language_de in work_language.lower():
                            work_title = work.get('title') or ''
                            if search_title_en in work_title.lower() or search_title_de in work_title.lower():
                                abstract = parse_abstract(work.get('abstract_inverted_index'))
                                print(work)
                                print(abstract)
'''

#'''
### loop version without language
i = 0
for update_folder in update_folders:
    gz_files = get_filenames(f'{openalex_works_folder}\\{update_folder}')
    for gz_file in gz_files:
        with gzip.open(f'{openalex_works_folder}\\{update_folder}\\{gz_file}', 'rt', encoding='utf-8') as lines:
            for line in lines:
                    work = json.loads(line)
                    work_type = work.get('type') or ''                    
                    if search_type in work_type.lower():
                        work_title = work.get('title') or ''
                        if search_title_en in work_title.lower() or search_title_de in work_title.lower():
                            #abstract = parse_abstract(work.get('abstract_inverted_index'))
                            #print(work)
                            #print(abstract)
                            i = i + 1
                            print(f'{i} article found. Latest in {openalex_works_folder}\\{update_folder}\\{gz_file}')
                            append_to_json("output.jsonl", line)

end_time = time.time()
end = datetime.fromtimestamp(end_time, tz=ZoneInfo("Europe/Berlin"))
print(end)

print("--- %s minutes ---" % ((end_time - start_time) / 60))

#'''

'''
### test version
i = 0
gz_file = get_filenames(f'{openalex_works_folder}\\{update_folders[0]}')
with gzip.open(f'{openalex_works_folder}\\{update_folders[0]}\\{gz_file[0]}', 'rt', encoding='utf-8') as lines:
    for line in lines:
        work = json.loads(line)
        title = work.get('title') or ''
        abstract = parse_abstract(work.get('abstract_inverted_index'))
        print(work)
        print(abstract)
        i = i + 1
        if i == 2:
            break
'''