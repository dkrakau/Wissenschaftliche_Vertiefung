import psycopg2
import math
import pandas as pd

from psycopg2.extensions import connection as PgConnection
from psycopg2.extras import Json

"""
############################################################################################
                                HELPER FUNCTIONS
############################################################################################
"""


def get_or_none(dataset: dict, key: str):
    result = None
    if key in dataset:
        value = dataset[key]
        is_nan_string = isinstance(value, str) and value.strip().lower() == "nan"
        is_float_nan = isinstance(value, float) and math.isnan(value)
        if value is not None and not is_nan_string and not is_float_nan:
            result = value
    return result


"""
############################################################################################
                                GET FUNCTIONS
############################################################################################
"""


def get_publication_year_by_work_doi(conn: PgConnection, doi: str):
    query = "SELECT publication_year FROM openalex.work WHERE doi = %s;"
    with conn.cursor() as cur:
        cur.execute(query, (doi,))
        row = cur.fetchone()
        return row[0] if row else None


def get_author_id(conn: PgConnection, display_name: str):
    query = "SELECT id FROM openalex.author WHERE display_name = %s;"
    with conn.cursor() as cur:
        cur.execute(query, (display_name,))
        row = cur.fetchone()
        return row[0] if row else None


"""
############################################################################################
                                DELETE FUNCTIONS
############################################################################################
"""


def delete_work_by_doi(conn: PgConnection, doi: str):
    sql = "DELETE FROM openalex.work WHERE doi = %s;"
    with conn.cursor() as cur:
        cur.execute(sql, (doi,))


"""
############################################################################################
                                INSERT FUNCTIONS
############################################################################################
"""


def insert_work_type(conn: PgConnection, dataset: dict, work_types: dict):
    # extract data
    work_type_id = dataset["type"]

    # insert all work_types if not already present
    if work_type_id:
        sql = """
            INSERT INTO work_type (id, display_description)
            VALUES (%s, %s)
            ON CONFLICT (id) DO NOTHING;
        """
        with conn.cursor() as cur:
            display_description = work_types.get(work_type_id)
            cur.execute(sql, (work_type_id, display_description))
        conn.commit()


def insert_languages(
    conn: PgConnection,
    dataset: dict,
    language_codes_aplpha2_types: dict,
    language_codes_aplpha3_types: dict,
):
    # extract data
    code_alpha_2_3 = get_or_none(dataset, "language")

    # insert all languages if not already present
    if code_alpha_2_3:
        sql = """
            INSERT INTO languages (code_alpha_2_3, display_name)
            VALUES (%s, %s)
            ON CONFLICT (code_alpha_2_3) DO NOTHING;
        """
        with conn.cursor() as cur:
            display_name = language_codes_aplpha2_types.get(
                code_alpha_2_3
            ) or language_codes_aplpha3_types.get(code_alpha_2_3)
            cur.execute(sql, (code_alpha_2_3, display_name))
        conn.commit()


def insert_work(conn: PgConnection, dataset: dict):
    # extract data
    work_id = dataset["id"].split("/")[-1]
    doi = get_or_none(dataset, "doi")
    type_id = dataset["type"]
    title = dataset["title"]
    publication_date = get_or_none(dataset, "publication_date")
    current_publication_year = get_or_none(dataset, "publication_year")
    language_code_alpha_2_3 = get_or_none(dataset, "language")
    abstract_inverted_index = Json(dataset["abstract_inverted_index"])
    cited_by_count = int(dataset["cited_by_count"])
    referenced_works_count = int(dataset["referenced_works_count"])
    authors_count = int(len(dataset["authorships"]))
    locations_count = int(dataset["locations_count"])
    is_open_access = bool(dataset["open_access"]["is_oa"])
    is_paratext = bool(dataset["is_paratext"])
    is_retracted = bool(dataset["is_retracted"])
    has_fulltext = bool(dataset["has_fulltext"])
    created_date = dataset["created_date"]
    updated_date = dataset["updated_date"]
    # Doupicate test: Check if current publication_year is newest
    publication_year = get_publication_year_by_work_doi(conn, doi)
    if publication_year is not None and publication_year >= current_publication_year:
        return  # skip if existing entrys publication year is newer.
    # drop older work
    if publication_year is not None:
        delete_work_by_doi(conn, doi)
    # insert current work
    sql = """
        INSERT INTO work (
            id,
            doi,
            type_id,
            title,
            publication_date,
            publication_year,
            language_code_alpha_2_3,
            abstract_inverted_index,
            cited_by_count,
            referenced_works_count,
            authors_count,
            locations_count,
            is_open_access,
            is_paratext,
            is_retracted,
            has_fulltext,
            created_date,
            updated_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    with conn.cursor() as cur:
        cur.execute(
            sql,
            (
                work_id,
                doi,
                type_id,
                title,
                publication_date,
                current_publication_year,
                language_code_alpha_2_3,
                abstract_inverted_index,
                cited_by_count,
                referenced_works_count,
                authors_count,
                locations_count,
                is_open_access,
                is_paratext,
                is_retracted,
                has_fulltext,
                created_date,
                updated_date,
            ),
        )
    conn.commit()


def insert_biblio(conn: PgConnection, dataset: dict):
    # extract data
    work_id = dataset["id"].split("/")[-1]
    biblio = dataset["biblio"]

    # insert biblio
    if biblio:
        sql = """
            INSERT INTO biblio (work_id, volume, issue, first_page, last_page)
            VALUES (%s, %s, %s, %s, %s);
        """
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    work_id,
                    biblio["volume"],
                    biblio["issue"],
                    biblio["first_page"],
                    biblio["last_page"],
                ),
            )
        conn.commit()


def insert_work_reference(conn: PgConnection, dataset: dict):
    # extract data
    work_id = dataset["id"].split("/")[-1]
    referenced_works = [rw.split("/")[-1] for rw in dataset["referenced_works"]]

    # insert work_reference if referenced_works is present in dataset
    if referenced_works:
        sql = """
            INSERT INTO work_reference (work_id, referenced_work_id)
            VALUES (%s, %s);
        """
        if referenced_works:
            with conn.cursor() as cur:
                for referenced_work in referenced_works:
                    cur.execute(sql, (work_id, referenced_work))
            conn.commit()


def insert_indexed_in(conn: PgConnection, dataset: dict, indexed_in_types: dict):
    # extract data
    indexed_in = dataset["indexed_in"]

    # insert all indexes if not already present
    if indexed_in:
        sql = """
            INSERT INTO indexed_in (id, display_name)
            VALUES (%s, %s)
            ON CONFLICT (id) DO NOTHING;
        """
        with conn.cursor() as cur:
            for index in indexed_in:
                display_name = indexed_in_types.get(index)
                cur.execute(sql, (index, display_name))
        conn.commit()


def insert_work_indexed_in(conn: PgConnection, dataset: dict):
    # extract data
    work_id = dataset["id"].split("/")[-1]
    indexed_in = dataset["indexed_in"]

    # insert work_indexed_in if indexed_in is present in dataset
    if indexed_in:
        sql = """
            INSERT INTO work_indexed_in (work_id, indexed_in_id)
            VALUES (%s, %s);
        """
        with conn.cursor() as cur:
            for index in indexed_in:
                cur.execute(sql, (work_id, index))
        conn.commit()


def insert_keyword(conn: PgConnection, dataset: dict):
    # extract data
    keywords = [
        (kw["id"].split("/")[-1], kw["display_name"]) for kw in dataset["keywords"]
    ]

    # insert all keywords if not already present
    if keywords:
        sql = """
            INSERT INTO keyword (id, display_name)
            VALUES (%s, %s)
            ON CONFLICT (id) DO NOTHING;
        """
        with conn.cursor() as cur:
            for id, display_name in keywords:
                cur.execute(sql, (id, display_name))
        conn.commit()


def insert_work_keyword(conn: PgConnection, dataset: dict):
    # extract data
    work_id = dataset["id"].split("/")[-1]
    keyword_ids_with_score = [
        (kw["id"].split("/")[-1], float(kw["score"])) for kw in dataset["keywords"]
    ]

    # insert work_keyword if keywords is present in dataset
    if keyword_ids_with_score:
        sql = """
            INSERT INTO work_keyword (work_id, keyword_id, score)
            VALUES (%s, %s, %s)
            ON CONFLICT (work_id, keyword_id) DO NOTHING;
        """
        with conn.cursor() as cur:
            for id, score in keyword_ids_with_score:
                cur.execute(sql, (work_id, id, score))
        conn.commit()


def insert_domain(conn: PgConnection, dataset: dict):
    # extract data
    domains = [
        (int(topic["domain"]["id"].split("/")[-1]), topic["domain"]["display_name"])
        for topic in dataset["topics"]
    ]

    # insert all domains if not already present
    if domains:
        sql = """
            INSERT INTO domain (id, display_name)
            VALUES (%s, %s)
            ON CONFLICT (id) DO NOTHING;
        """
        with conn.cursor() as cur:
            for id, display_name in domains:
                cur.execute(sql, (id, display_name))
        conn.commit()


def insert_field(conn: PgConnection, dataset: dict):
    # extract data
    fields = [
        (
            int(topic["field"]["id"].split("/")[-1]),
            int(topic["domain"]["id"].split("/")[-1]),
            topic["field"]["display_name"],
        )
        for topic in dataset["topics"]
    ]

    # insert all fields if not already present
    if fields:
        sql = """
            INSERT INTO field (id, domain_id, display_name)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO NOTHING;
        """
        with conn.cursor() as cur:
            for id, domain_id, display_name in fields:
                cur.execute(sql, (id, domain_id, display_name))
        conn.commit()


def insert_subfield(conn: PgConnection, dataset: dict):
    # extract data
    subfields = [
        (
            int(topic["subfield"]["id"].split("/")[-1]),
            int(topic["field"]["id"].split("/")[-1]),
            topic["subfield"]["display_name"],
        )
        for topic in dataset["topics"]
    ]

    # insert sll subfields if not already present
    if subfields:
        sql = """
            INSERT INTO subfield (id, field_id, display_name)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO NOTHING;
        """
        with conn.cursor() as cur:
            for id, field_id, display_name in subfields:
                cur.execute(sql, (id, field_id, display_name))
        conn.commit()


def insert_topic(conn: PgConnection, dataset: dict):
    # extract data
    topics = [
        (
            topic["id"].split("/")[-1],
            int(topic["subfield"]["id"].split("/")[-1]),
            topic["display_name"],
        )
        for topic in dataset["topics"]
    ]

    # insert all topics if not already present
    if topics:
        sql = """
            INSERT INTO topic (id, subfield_id, display_name)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO NOTHING;
        """
        with conn.cursor() as cur:
            for id, subfield_id, display_name in topics:
                cur.execute(sql, (id, subfield_id, display_name))
        conn.commit()


def insert_work_topic(conn: PgConnection, dataset: dict):
    # extract data
    work_id = dataset["id"].split("/")[-1]
    topics = [
        (topic["id"].split("/")[-1], float(topic["score"]))
        for topic in dataset["topics"]
    ]

    # insert work_topic if topics is present in dataset
    if topics:
        sql = """
            INSERT INTO work_topic (work_id, topic_id, score)
            VALUES (%s, %s, %s)
            ON CONFLICT (work_id, topic_id) DO NOTHING;
        """
        with conn.cursor() as cur:
            for topic_id, score in topics:
                cur.execute(sql, (work_id, topic_id, score))
        conn.commit()


def insert_country(conn: PgConnection, dataset: dict, country_types: dict):
    # extract data
    codes_alpha_2 = set()
    for authorship in dataset["authorships"]:
        for country in authorship["countries"]:
            codes_alpha_2.add(country)

    # insert all countrys if not already present
    if codes_alpha_2:
        sql = """
            INSERT INTO country (code_alpha_2, display_name)
            VALUES (%s, %s)
            ON CONFLICT (code_alpha_2) DO NOTHING;
        """
        with conn.cursor() as cur:
            for code_alpha_2 in codes_alpha_2:
                display_name = country_types.get(code_alpha_2)
                cur.execute(sql, (code_alpha_2, display_name))
        conn.commit()


def insert_author(conn: PgConnection, dataset: dict):
    # extract data
    authors = [
        (
            (
                authorship["author"]["id"].split("/")[-1]
                if authorship["author"]["id"]
                else None
            ),
            authorship["author"]["display_name"],
            authorship["author"]["orcid"],
        )
        for authorship in dataset["authorships"]
    ]

    # insert all authors if not already present
    if authors:
        sql = """
            INSERT INTO author (openalex_id, display_name, orcid)
            VALUES (%s, %s, %s)
            ON CONFLICT (display_name) DO NOTHING;
        """
        with conn.cursor() as cur:
            for openalex_id, display_name, orcid in authors:
                cur.execute(sql, (openalex_id, display_name, orcid))
        conn.commit()


def insert_author_country(conn: PgConnection, dataset: dict):
    # extract data
    author_counties = set()
    for authorship in dataset["authorships"]:
        author_id = get_author_id(conn, authorship["author"]["display_name"])
        for country in authorship["countries"]:
            author_counties.add((author_id, country))
    # insert all author_counties if not already present
    if author_counties:
        sql = """
            INSERT INTO author_country (author_id, country_code_alpha_2)
            VALUES (%s, %s)
            ON CONFLICT (author_id, country_code_alpha_2) DO NOTHING;
        """
        with conn.cursor() as cur:
            for author_country in author_counties:
                cur.execute(sql, (author_country[0], author_country[1]))
        conn.commit()


def insert_institution_type(conn: PgConnection, dataset: dict, institute_types: dict):
    # extract data
    institution_type_ids = set()
    for authorship in dataset["authorships"]:
        for institution in authorship["institutions"]:
            if institution["type"] is not None:
                institution_type_ids.add(institution["type"])

    # insert all institution_types if not already present
    if institution_type_ids:
        sql = """
            INSERT INTO institution_type (id, display_name)
            VALUES (%s, %s)
            ON CONFLICT (id) DO NOTHING;
        """
        with conn.cursor() as cur:
            for institution_type_id in institution_type_ids:
                display_name = institute_types.get(institution_type_id)
                cur.execute(sql, (institution_type_id, display_name))
        conn.commit()


def insert_institution(conn: PgConnection, dataset: dict):
    # extract data
    institutions = set()
    for authorship in dataset["authorships"]:
        for institution in authorship["institutions"]:
            institutions.add(
                (
                    institution["id"].split("/")[-1],
                    institution["display_name"],
                    institution["ror"],
                    institution["type"],
                    institution["country_code"],
                )
            )

    # insert all institutions if not already present
    if institutions:
        sql = """
            INSERT INTO institution (id, display_name, ror, institution_type_id, country_code_alpha_2)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING;
        """
        with conn.cursor() as cur:
            for (
                id,
                display_name,
                ror,
                institution_type_id,
                country_code_alpha_2,
            ) in institutions:
                cur.execute(
                    sql,
                    (id, display_name, ror, institution_type_id, country_code_alpha_2),
                )
        conn.commit()


def insert_work_author(conn: PgConnection, dataset: dict):
    # extract data
    work_id = dataset["id"].split("/")[-1]
    authors = [
        get_author_id(conn, author["author"]["display_name"])
        for author in dataset["authorships"]
    ]

    # insert work_author if authors are present in dataset
    if not all(a is None for a in authors):
        sql = """
            INSERT INTO work_author (work_id, author_id)
            VALUES (%s, %s)
            ON CONFLICT (work_id, author_id) DO NOTHING;
        """
        with conn.cursor() as cur:
            for author_id in authors:
                cur.execute(sql, (work_id, author_id))
        conn.commit()


def insert_work_author_institution(conn: PgConnection, dataset: dict):
    # extract data
    work_id = dataset["id"].split("/")[-1]
    author_institutions = set()
    for authorship in dataset["authorships"]:
        author_id = get_author_id(conn, authorship["author"]["display_name"])
        for institution in authorship["institutions"]:
            author_institutions.add((author_id, institution["id"].split("/")[-1]))

    # insert work_author_institution if author_institutions is not emtpy
    if author_institutions:
        sql = """
            INSERT INTO work_author_institution (work_id, author_id, institution_id)
            VALUES (%s, %s, %s);
        """
        with conn.cursor() as cur:
            for author_id, institution_id in author_institutions:
                cur.execute(sql, (work_id, author_id, institution_id))
        conn.commit()


def insert_funder(conn: PgConnection, dataset: dict):
    # extract data
    funders = dataset["funders"]

    # insert all funders if not already present
    if funders:
        sql = """
            INSERT INTO funder (id, display_name, ror)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO NOTHING;
        """
        with conn.cursor() as cur:
            for funder in funders:
                cur.execute(
                    sql,
                    (
                        funder["id"].split("/")[-1],
                        funder["display_name"],
                        funder["ror"],
                    ),
                )
        conn.commit()


def insert_work_funder(conn: PgConnection, dataset: dict):
    # extract data
    work_id = dataset["id"]
    funders = dataset["funders"]

    # insert work_funder if funders are present in dataset
    if funders:
        sql = """
            INSERT INTO work_funder (work_id, funder_id)
            VALUES (%s, %s);
        """
        with conn.cursor() as cur:
            for funder in funders:
                cur.execute(
                    sql,
                    (work_id.split("/")[-1], funder["id"].split("/")[-1]),
                )
        conn.commit()


def insert_work_award(conn: PgConnection, dataset: dict):
    # extract data
    work_id = dataset["id"]
    awards = dataset["awards"]

    # insert work_award if awards are present in dataset
    if awards:
        sql = """
            INSERT INTO work_award (work_id, award_id)
            VALUES (%s, %s);
        """
        with conn.cursor() as cur:
            for award in awards:
                cur.execute(
                    sql,
                    (work_id.split("/")[-1], award["id"].split("/")[-1]),
                )
        conn.commit()


def insert_source_type(conn: PgConnection, dataset: dict, source_types: dict):
    # extract data
    source_type_ids = set()
    for location in dataset["locations"]:
        source = location["source"]
        if source is not None:
            source_type_ids.add(source["type"])

    # insert all source_types if not already present
    if source_type_ids:
        sql = """
            INSERT INTO source_type (id, display_name)
            VALUES (%s, %s)
            ON CONFLICT (id) DO NOTHING;
        """
        with conn.cursor() as cur:
            for source_type_id in source_type_ids:
                display_name = source_types.get(source_type_id)
                cur.execute(sql, (source_type_id, display_name))
        conn.commit()


def insert_source(conn: PgConnection, dataset: dict):
    # extract data
    sources = set()
    for location in dataset["locations"]:
        source = location["source"]

        if source is not None:
            host_organisation = None
            host_organisation_name = None
            if "host_organisation" in source:
                host_organisation = source["host_organisation"].split("/")[-1]
            if "host_organisation_name" in source:
                host_organisation_name = source["host_organisation_name"]

            sources.add(
                (
                    source["id"].split("/")[-1],
                    source["issn_l"],
                    source["display_name"],
                    host_organisation,
                    host_organisation_name,
                    source["type"],
                    source["is_oa"],
                )
            )

        # insert all sources if not already present
        if sources:
            sql = """
                INSERT INTO source (
                    id,
                    issn_l,
                    display_name,
                    host_organisation,
                    host_organisation_name,
                    source_type_id,
                    is_open_access)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING;
            """
            with conn.cursor() as cur:
                for (
                    id,
                    issn_l,
                    display_name,
                    host_organisation,
                    host_organisation_name,
                    source_type_id,
                    is_open_access,
                ) in sources:
                    cur.execute(
                        sql,
                        (
                            id,
                            issn_l,
                            display_name,
                            host_organisation,
                            host_organisation_name,
                            source_type_id,
                            is_open_access,
                        ),
                    )
            conn.commit()


def insert_versions(conn: PgConnection, dataset: dict, version_types: dict):
    # extract data
    version_type_ids = set()
    for location in dataset["locations"]:
        if location["version"] != None:
            version_type_ids.add(location["version"])

    # insert all versions if not already present
    if version_type_ids:
        sql = """
            INSERT INTO versions (id, display_description)
            VALUES (%s, %s)
            ON CONFLICT (id) DO NOTHING;
        """
        with conn.cursor() as cur:
            for version_type_id in version_type_ids:
                display_description = version_types.get(version_type_id)
                cur.execute(sql, (version_type_id, display_description))
        conn.commit()


def insert_license(conn: PgConnection, dataset: dict, license_types: dict):
    # extract data
    license_type_ids = set()
    for location in dataset["locations"]:
        if location["license_id"] != None:
            license_type_ids.add(location["license_id"].split("/")[-1])

    # insert all license if not already present
    if license_type_ids:
        sql = """
            INSERT INTO license (id, display_name)
            VALUES (%s, %s)
            ON CONFLICT (id) DO NOTHING;
        """
        with conn.cursor() as cur:
            for license_type_id in license_type_ids:
                display_name = license_types.get(license_type_id)
                cur.execute(sql, (license_type_id, display_name))
        conn.commit()


def insert_locations(conn: PgConnection, dataset: dict):
    # extract data
    locations_by_id = {}
    for location in dataset["locations"]:
        source = location["source"]
        locations_by_id[location["id"]] = (
            location["id"],
            (
                source["id"].split("/")[-1]
                if source is not None and source["id"]
                else None
            ),
            location["pdf_url"],
            location["landing_page_url"],
            location["version"],
            (location["license_id"].split("/")[-1] if location["license_id"] else None),
            location["is_oa"],
            location["is_accepted"],
            location["is_published"],
        )
    locations = list(locations_by_id.values())  # to remove location duplicates by id

    # insert locations if locations are present in dataset
    if locations:
        sql = """
            INSERT INTO locations (
                id,
                source_id,
                pdf_url,
                landing_page_url,
                version_id,
                license_id,
                is_open_access,
                is_accepted,
                is_published)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING;
        """
        with conn.cursor() as cur:
            for (
                id,
                source_id,
                pdf_url,
                landing_page_url,
                version_id,
                license_id,
                is_open_access,
                is_accepted,
                is_published,
            ) in locations:
                cur.execute(
                    sql,
                    (
                        id,
                        source_id,
                        pdf_url,
                        landing_page_url,
                        version_id,
                        license_id,
                        is_open_access,
                        is_accepted,
                        is_published,
                    ),
                )
        conn.commit()


def insert_work_locations(conn: PgConnection, dataset: dict):
    # extract data
    work_id = dataset["id"].split("/")[-1]
    locations = [(location["id"], False) for location in dataset["locations"]]

    # insert work_locations if locations are present in dataset
    if locations:
        locations[0] = (locations[0][0], True)  # set frist tuple as primary location
        sql = """
            INSERT INTO work_locations (work_id, locations_id, is_primary)
            VALUES (%s, %s, %s)
            ON CONFLICT (work_id, locations_id) DO NOTHING;
        """
        with conn.cursor() as cur:
            for locations_id, is_primary in locations:
                cur.execute(sql, (work_id, locations_id, is_primary))
        conn.commit()
