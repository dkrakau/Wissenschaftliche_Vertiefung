import sys
import argparse
import json
import pandas as pd
from scripts.config import load_config
from scripts.connect import connect
from scripts.load_types import *
from scripts.inserts import *

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

    '''
    # load db config data
    config = load_config()
    # connect to posgres db
    conn = connect(config)
    '''

    # load openalex types
    work_types = load_work_types()
    institution_types = load_institution_types()
    source_types = load_soure_types()
    license_types = load_license_types()
    version_types = load_version_types()
    indexed_in_types = load_indexed_in_types()
    language_types = load_language_types()
    country_types = load_country_types()

    # loading openalex work objects into pandas
    df = pd.read_json(args.file, lines=True)
    for dataset in df.to_dict(orient="records"):
        # inserts
        '''
        insert_work_type(conn, dataset, work_types)
        insert_languages(conn, dataset, language_types)
        insert_work(conn, dataset)
        insert_biblio(conn, dataset)
        insert_work_reference(conn, dataset)
        insert_indexed_in(conn, dataset, indexed_in_types)
        insert_work_indexed_in(conn, dataset)
        insert_keyword(conn, dataset)
        insert_work_keyword(conn, dataset)
        insert_domain(conn, dataset)
        insert_field(conn, dataset)
        insert_subfield(conn, dataset)
        insert_topic(conn, dataset)
        insert_work_topic(conn, dataset)
        insert_country(conn, dataset, country_types)
        insert_author(conn, dataset)
        insert_author_country(conn, dataset)
        insert_institution_type(conn, dataset, institution_types)
        insert_institution(conn, dataset)
        insert_work_author(conn, dataset)
        insert_work_author_institution(conn, dataset)
        insert_funder(conn, dataset)
        insert_work_funder(conn, dataset)
        insert_work_award(conn, dataset)
        insert_source_type(conn, dataset, source_types)
        insert_source(conn, dataset)
        insert_versions(conn, dataset, version_types)
        insert_license(conn, dataset, license_types)
        insert_locations(conn, dataset)
        insert_work_locations(conn, dataset)
        '''

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

# cd database
# python importer.py ../openalex/result-2026-08-01_11-14-41.jsonl