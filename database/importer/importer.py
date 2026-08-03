import sys
import argparse
import json
import pandas as pd
import psycopg2

def read_work_types(): 
    with open("work_tpyes.json", "r", encoding="utf-8") as f:
        return json.load(f)

def read_institution_types(): 
    with open("institution_tpyes.json", "r", encoding="utf-8") as f:
        return json.load(f)

def read_soure_types(): 
    with open("source_tpyes.json", "r", encoding="utf-8") as f:
        return json.load(f)

def read_license_types(): 
    with open("license_tpyes.json", "r", encoding="utf-8") as f:
        return json.load(f)

def read_version_types(): 
    with open("version_tpyes.json", "r", encoding="utf-8") as f:
        return json.load(f)

def read_language_types(): 
    with open("iso-639-1-alpha-2-language-code_types.json", "r", encoding="utf-8") as f:
        return json.load(f)

def read_country_types(): 
    with open("iso-3166-1-alpha-2-country-code_types.json", "r", encoding="utf-8") as f:
        return json.load(f)

def parse_abstract(inverted_index: dict) -> str:
    if not inverted_index:
        return ""

    max_pos = max(pos for positions in inverted_index.values() for pos in positions)

    words = [""] * (max_pos + 1)
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word

    return " ".join(words)

def main():
    parser = argparse.ArgumentParser(description="Process a JSONL file.")
    parser.add_argument("file", help="Path to the .jsonl file to process")
    args = parser.parse_args()

    file = args.file

    # openalex types
    work_types = read_work_types()
    institution_types = read_institution_types()
    source_types = read_soure_types()
    license_types = read_license_types()
    version_types = read_version_types()
    language_types = read_language_types()
    country_types = read_country_types()

    # reading openalex work objects
    df = pd.read_json(file, lines=True)
    



    ###################################################################################################################################

    ''' dataset by index
    dataset = df.to_dict(orient="records")
    print(dataset[113])
    '''

    ''' institutions of authorship
    for dataset in df.to_dict(orient="records"):
        if [author["institutions"] for author in dataset["authorships"]] != []:
            print(dataset)
            break
    '''

    ''' institutions | not exists in hole data
    for dataset in df.to_dict(orient="records"):
        if dataset["institutions"] != []:
            print(dataset)
            break
    '''

    ''' funders
    for dataset in df.to_dict(orient="records"):
        if dataset["funders"] != []:
            print(dataset)
            break
    '''

    #''' awards
    for dataset in df.to_dict(orient="records"):
        if dataset["awards"] != []:
            print(dataset)
            break
    #'''

    ''' awards, funders one  of them is missing
    for dataset in df.to_dict(orient="records"):
        if dataset["awards"] != [] and dataset["funders"] == []:
            print(dataset)
            break
    '''
    ''' funders, awards one  of them is missing
    for dataset in df.to_dict(orient="records"):
        if dataset["funders"] != [] and dataset["awards"] == []:
            print(dataset)
            break
    '''

    # specifies keys for locations
    location = "primary_location"  # if is_oa = false
    #location = "best_oa_location" # if is_oa = true

    # table work
    work_id = dataset["id"]
    doi = dataset["doi"]
    title = dataset["title"]
    display_name = dataset["display_name"]
    publication_date = dataset["publication_date"]
    publication_year = dataset["publication_year"]
    language = dataset["language"]
    work_type = dataset["type"]
    abstract_inverted_index = dataset["abstract_inverted_index"]
    keywords = [keyword["display_name"] for keyword in dataset["keywords"]]
    cited_by_count = dataset["cited_by_count"]
    authors_count = dataset["authors_count"]
    # maybe rework? own table for domain -> discipline?
    primary_topic = dataset["primary_topic"]["display_name"]
    subfield = dataset["primary_topic"]["subfield"]["display_name"]
    field = dataset["primary_topic"]["field"]["display_name"]
    domain = dataset["primary_topic"]["domain"]["display_name"]
    pdf_url = dataset[location]["pdf_url"]
    landing_page_url = dataset[location]["landing_page_url"]
    is_oa = dataset["open_access"]["is_oa"]
    is_accepted = dataset[location]["is_accepted"]
    is_published = dataset[location]["is_published"]
    version = dataset[location]["version"]
    
    # table source
    issn_l = dataset[location]["source"]["issn_l"]
    source_type = dataset[location]["source"]["type"]
    display_name = dataset[location]["source"]["type"]
    host_organisation_name = dataset[location]["source"]["host_organization_name"]

    # table license
    license_id = dataset[location]["license_id"]
    license = dataset[location]["license"]

    # table biblio
    biblio_volume = dataset["biblio"]["volume"]
    biblio_issue = dataset["biblio"]["issue"]
    biblio_first_page = dataset["biblio"]["first_page"]
    biblio_last_page = dataset["biblio"]["last_page"]
    
    # table author
    # add language to authors? combine institutions and authors?
    author_names = [author["author"]["display_name"] for author in dataset["authorships"]]
    orcid = [author["author"]["orcid"] for author in dataset["authorships"]]


if __name__ == '__main__':
    main()

# cd .\database\importer
# python importer.py ../../openalex/result-2026-08-01_11-14-41.jsonl