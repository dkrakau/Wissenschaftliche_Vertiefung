import argparse
import pandas as pd
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from scripts.config import load_config
from scripts.connect import connect
from scripts.load_types import *
from scripts.db_inserts import *
from scripts.utils import *
from urllib.parse import urlsplit, urlunsplit


def main():
    parser = argparse.ArgumentParser(description="Process a JSONL file.")
    parser.add_argument("file", help="Path to the .jsonl file to process")
    args = parser.parse_args()

    # load db config data
    config = load_config("scripts/database.ini")
    # connect to posgres db
    conn = connect(config)

    # load openalex types
    work_types = load_work_types()
    institution_types = load_institution_types()
    source_types = load_soure_types()
    license_types = load_license_types()
    version_types = load_version_types()
    indexed_in_types = load_indexed_in_types()
    language_codes_aplpha2_types = load_language_codes_aplpha2_types()
    language_codes_aplpha3_types = load_language_codes_aplpha3_types()
    country_types = load_country_types()

    print(f"Start importing data from {args.file} to database ...")

    start_timestamp = time.time()
    start_time = datetime.fromtimestamp(
        start_timestamp, tz=ZoneInfo("Europe/Berlin")
    ).strftime("%Y-%m-%d_%H-%M-%S")
    print(f"Start time: {start_time}")

    # loading openalex work objects into pandas
    df = pd.read_json(args.file, lines=True)
    line_counts = len(df)
    i = 0
    for dataset in df.to_dict(orient="records"):
        # for i, dataset in enumerate(df.iloc[3780:].to_dict(orient="records"), start=3781):  # for debugging

        # Convert work url to api work url
        url = dataset["id"]
        parts = urlsplit(url)
        parts = parts._replace(netloc="api." + parts.netloc)
        work_api_url = urlunsplit(parts)

        print(work_api_url, end=" ")

        # inserts
        insert_work_type(conn, dataset, work_types)
        insert_languages(
            conn, dataset, language_codes_aplpha2_types, language_codes_aplpha3_types
        )
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

        i = i + 1
        print(f"processed ({i}/{line_counts})")

    # Calculate script run time
    end_timestamp = time.time()
    end_time = datetime.fromtimestamp(
        end_timestamp, tz=ZoneInfo("Europe/Berlin")
    ).strftime("%Y-%m-%d_%H-%M-%S")
    print(f"Start time: {start_time}")
    print(f"End time:   {end_time}")
    print("Total minutes: %s" % ((end_timestamp - start_timestamp) / 60))


if __name__ == "__main__":
    main()

# cd database
# python importer.py ../openalex/result-2026-08-01_11-14-41.jsonl
