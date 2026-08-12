import psycopg2
import math
import pandas as pd
from datetime import datetime, timezone
from psycopg2.extensions import connection as PgConnection
from psycopg2.extras import RealDictCursor
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


def parse_datetime_utc(s: str) -> datetime:
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def clean_up(conn: PgConnection):
    delete_unreferenced_indexes(conn)
    delete_unreferenced_authors(conn)
    delete_unreferenced_institutions(conn)
    delete_unreferenced_funders(conn)
    delete_unreferenced_keywords(conn)
    delete_unreferenced_locations(conn)
    delete_unreferenced_topics(conn)

    delete_unreferenced_institution_types(conn)
    delete_unreferenced_countries(conn)
    delete_unreferenced_sources(conn)
    delete_unreferenced_licenses(conn)
    delete_unreferenced_versions(conn)
    delete_unreferenced_subfields(conn)

    delete_unreferenced_source_types(conn)
    delete_unreferenced_fields(conn)

    delete_unreferenced_domain(conn)

    delete_unreferenced_work_types(conn)
    delete_unreferenced_languages(conn)

    delete_unreferenced_work_references(conn)


"""
############################################################################################
                                SKIP FUNCTIONS
############################################################################################
"""


def skip_work(conn: PgConnection, dataset: dict) -> bool:
    # extract data
    work_id = dataset["id"].split("/")[-1]
    doi = get_or_none(dataset, "doi")
    title = dataset["title"]
    current_publication_date = get_or_none(dataset, "publication_date")
    current_publication_year = get_or_none(dataset, "publication_year")
    current_authors_count = len(dataset["authorships"])
    current_updated_date = dataset["updated_date"]
    # Duplication check 1: same DOI
    publication_year = get_publication_year_by_work_doi(conn, doi)
    if publication_year is not None:  # same DOI exists
        if publication_year >= current_publication_year:
            print(f"\nskip current work with id {work_id}")
            return True  # keep work with existing DOI
        delete_work_by_doi(conn, doi)  # delete existing work
        print(f"\ndeleted existing work with doi: {doi}")
    # Duplication check 2: same normalized title
    if exists_normalized_title(conn, title):  # same title exists
        existing_work = get_work_by_title(conn, title)
        if current_publication_date is not None:
            comparisons = [
                (
                    "publication_date",
                    existing_work["publication_date"],
                    parse_datetime_utc(current_publication_date),
                ),
                (
                    "authors_count",
                    existing_work["authors_count"],
                    current_authors_count,
                ),
                (
                    "updated_date",
                    existing_work["updated_date"],
                    parse_datetime_utc(current_updated_date),
                ),
            ]
            for fieldname, existing_value, current_value in comparisons:
                if current_value > existing_value:
                    delete_work_by_id(conn, existing_work["id"])
                    print(
                        f'\ndeleted work {existing_work["id"]} with older values for {fieldname}.'
                    )
                    break
                if current_value < existing_value:
                    print(
                        f'\nexisting work with id {existing_work["id"]} wins over compairissons.'
                    )
                    return True  # existing work wins over compairisons
            else:
                print(
                    f'\nexisting work with id {existing_work["id"]} wins (all fields compared).'
                )
                return True  # all fields compared keep existing work
        else:
            print(
                f'\nskip work with id {existing_work["id"]} because publication date is None.'
            )
            return True  # skip work with publication_date is None
    return False  # insert work


"""
############################################################################################
                                QUERY FUNCTIONS
############################################################################################
"""


def exists_normalized_title(conn: PgConnection, title: str) -> bool:
    query = "SELECT EXISTS ( SELECT 1 FROM openalex.work WHERE lower(trim(title)) = lower(trim(%s)) );"
    with conn.cursor() as cur:
        cur.execute(query, (title,))
        return cur.fetchone()[0]


def exists_work_id(conn: PgConnection, work_id: str) -> bool:
    query = "SELECT EXISTS ( SELECT 1 FROM openalex.work WHERE id = %s );"
    with conn.cursor() as cur:
        cur.execute(query, (work_id,))
        return cur.fetchone()[0]


def exists_institution_id(conn: PgConnection, institution_id: str) -> bool:
    query = "SELECT EXISTS ( SELECT 1 FROM openalex.institution WHERE id = %s );"
    with conn.cursor() as cur:
        cur.execute(query, (institution_id,))
        return cur.fetchone()[0]


def find_funder_by_ror(conn: PgConnection, ror: str) -> str:
    query = "SELECT id FROM openalex.funder WHERE ror = %s;"
    with conn.cursor() as cur:
        cur.execute(query, (ror,))
        row = cur.fetchone()
        if row is None:
            return None
        return row[0]


def exists_source_id(conn: PgConnection, source_id: str) -> bool:
    query = "SELECT EXISTS ( SELECT 1 FROM openalex.source WHERE id = %s );"
    with conn.cursor() as cur:
        cur.execute(query, (source_id,))
        return cur.fetchone()[0]


def exists_location_id(conn: PgConnection, location_id: str) -> bool:
    query = "SELECT EXISTS ( SELECT 1 FROM openalex.locations WHERE id = %s );"
    with conn.cursor() as cur:
        cur.execute(query, (location_id,))
        return cur.fetchone()[0]


def get_work_by_title(conn: PgConnection, title: str) -> dict | None:
    query = "SELECT * FROM openalex.work WHERE lower(trim(title)) = lower(trim(%s));"
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (title,))
        result = cur.fetchone()
        return dict(result) if result is not None else None


def get_publication_year_by_work_doi(conn: PgConnection, doi: str):
    query = "SELECT publication_year FROM openalex.work WHERE doi = %s;"
    with conn.cursor() as cur:
        cur.execute(query, (doi,))
        row = cur.fetchone()
        return row[0] if row else None


def get_author_id_by_orcid_and_openalex_id(
    conn: PgConnection, orcid: str, openalex_id: str
):
    query = "SELECT id FROM openalex.author WHERE orcid = %s OR (orcid IS NULL AND openalex_id = %s);"
    with conn.cursor() as cur:
        cur.execute(
            query,
            (
                orcid,
                openalex_id,
            ),
        )
        row = cur.fetchone()
        return row[0] if row else None


def get_author_id_by_display_name(conn: PgConnection, display_name: str):
    query = "SELECT id FROM openalex.author WHERE display_name = %s;"
    with conn.cursor() as cur:
        cur.execute(
            query,
            (display_name,),
        )
        row = cur.fetchone()
        return row[0] if row else None


def get_author_id_by_display_name_and_institutions(
    conn: PgConnection, display_name: str, institution_ids: list
):
    if not institution_ids:
        return None

    query = """
        SELECT DISTINCT a.id
        FROM openalex.author a
        JOIN openalex.work_author_institution wai ON wai.author_id = a.id
        WHERE LOWER(TRIM(a.display_name)) = LOWER(TRIM(%s))
            AND wai.institution_id = ANY(%s)
            AND a.openalex_id IS NULL;
    """
    with conn.cursor() as cur:
        cur.execute(query, (display_name, institution_ids))
        rows = cur.fetchall()

        if not rows:
            return None

        if len(rows) > 1:
            print(
                f"WARNING: ambiguous match for '{display_name}' -> {len(rows)} candidates: {[r[0] for r in rows]}"
            )
        return rows[0][0]


"""
############################################################################################
                                DELETE FUNCTIONS
############################################################################################
"""


def delete_work_by_id(conn: PgConnection, work_id: str):
    sql = "DELETE FROM openalex.work WHERE id = %s;"
    with conn.cursor() as cur:
        cur.execute(sql, (work_id,))
    conn.commit()


def delete_work_by_doi(conn: PgConnection, doi: str):
    sql = "DELETE FROM openalex.work WHERE doi = %s;"
    with conn.cursor() as cur:
        cur.execute(sql, (doi,))
    conn.commit()


def delete_unreferenced_indexes(conn: PgConnection):
    sql = "DELETE FROM openalex.indexed_in WHERE NOT EXISTS (SELECT 1 FROM openalex.work_indexed_in wii WHERE wii.indexed_in_id = indexed_in.id);"
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def delete_unreferenced_authors(conn: PgConnection):
    sql = "DELETE FROM openalex.author WHERE NOT EXISTS (SELECT 1 FROM openalex.work_author wa WHERE wa.author_id = author.id);"
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def delete_unreferenced_institutions(conn: PgConnection):
    sql = "DELETE FROM openalex.institution WHERE NOT EXISTS (SELECT 1 FROM openalex.work_author_institution wai WHERE wai.institution_id = institution.id);"
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def delete_unreferenced_institution_types(conn: PgConnection):
    sql = "DELETE FROM openalex.institution_type WHERE NOT EXISTS (SELECT 1 FROM openalex.institution i WHERE i.institution_type_id = institution_type.id);"
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def delete_unreferenced_countries(conn: PgConnection):
    sql = "DELETE FROM openalex.country WHERE NOT EXISTS (SELECT 1 FROM openalex.author_country ac WHERE ac.country_code_alpha_2 = country.code_alpha_2) AND NOT EXISTS (SELECT 1 FROM openalex.institution i WHERE i.country_code_alpha_2 = country.code_alpha_2);"
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def delete_unreferenced_funders(conn: PgConnection):
    sql = "DELETE FROM openalex.funder WHERE NOT EXISTS (SELECT 1 FROM openalex.work_funder wf WHERE wf.funder_id = funder.id);"
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def delete_unreferenced_keywords(conn: PgConnection):
    sql = "DELETE FROM openalex.keyword WHERE NOT EXISTS (SELECT 1 FROM openalex.work_keyword wk WHERE wk.keyword_id = keyword.id);"
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def delete_unreferenced_locations(conn: PgConnection):
    sql = "DELETE FROM openalex.locations WHERE NOT EXISTS (SELECT 1 FROM openalex.work_locations wl WHERE wl.locations_id = locations.id);"
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def delete_unreferenced_sources(conn: PgConnection):
    sql = "DELETE FROM openalex.source WHERE NOT EXISTS (SELECT 1 FROM openalex.locations lo WHERE lo.source_id = source.id);"
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def delete_unreferenced_source_types(conn: PgConnection):
    sql = "DELETE FROM openalex.source_type WHERE NOT EXISTS (SELECT 1 FROM openalex.source s WHERE s.source_type_id = source_type.id);"
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def delete_unreferenced_licenses(conn: PgConnection):
    sql = "DELETE FROM openalex.license WHERE NOT EXISTS (SELECT 1 FROM openalex.locations lo WHERE lo.license_id = license.id);"
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def delete_unreferenced_versions(conn: PgConnection):
    sql = "DELETE FROM openalex.versions WHERE NOT EXISTS (SELECT 1 FROM openalex.locations lo WHERE lo.version_id = versions.id);"
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def delete_unreferenced_work_types(conn: PgConnection):
    sql = "DELETE FROM openalex.work_type WHERE NOT EXISTS (SELECT 1 FROM openalex.work w WHERE w.type_id = work_type.id);"
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def delete_unreferenced_languages(conn: PgConnection):
    sql = "DELETE FROM openalex.languages WHERE NOT EXISTS (SELECT 1 FROM openalex.work w WHERE w.language_code_alpha_2_3 = languages.code_alpha_2_3);"
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def delete_unreferenced_topics(conn: PgConnection):
    sql = "DELETE FROM openalex.topic WHERE NOT EXISTS (SELECT 1 FROM openalex.work_topic wt WHERE wt.topic_id = topic.id);"
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def delete_unreferenced_subfields(conn: PgConnection):
    sql = "DELETE FROM openalex.subfield WHERE NOT EXISTS (SELECT 1 FROM openalex.topic t WHERE t.subfield_id = subfield.id);"
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def delete_unreferenced_fields(conn: PgConnection):
    sql = "DELETE FROM openalex.field WHERE NOT EXISTS (SELECT 1 FROM openalex.subfield sf WHERE sf.field_id = field.id);"
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def delete_unreferenced_domain(conn: PgConnection):
    sql = "DELETE FROM openalex.domain WHERE NOT EXISTS (SELECT 1 FROM openalex.field f WHERE f.domain_id = domain.id);"
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def delete_unreferenced_work_references(conn: PgConnection):
    sql = "DELETE FROM openalex.work_reference WHERE NOT EXISTS (SELECT 1 FROM openalex.work w WHERE w.id = work_reference.referenced_work_id);"
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


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
    current_publication_date = get_or_none(dataset, "publication_date")
    current_publication_year = get_or_none(dataset, "publication_year")
    language_code_alpha_2_3 = get_or_none(dataset, "language")
    abstract_inverted_index = Json(dataset["abstract_inverted_index"])
    cited_by_count = int(dataset["cited_by_count"])
    referenced_works_count = int(dataset["referenced_works_count"])
    current_authors_count = int(len(dataset["authorships"]))
    locations_count = int(dataset["locations_count"])
    is_open_access = bool(dataset["open_access"]["is_oa"])
    is_paratext = bool(dataset["is_paratext"])
    is_retracted = bool(dataset["is_retracted"])
    has_fulltext = bool(dataset["has_fulltext"])
    created_date = dataset["created_date"]
    current_updated_date = dataset["updated_date"]

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
                current_publication_date,
                current_publication_year,
                language_code_alpha_2_3,
                abstract_inverted_index,
                cited_by_count,
                referenced_works_count,
                current_authors_count,
                locations_count,
                is_open_access,
                is_paratext,
                is_retracted,
                has_fulltext,
                created_date,
                current_updated_date,
            ),
        )
    conn.commit()


def insert_biblio(conn: PgConnection, dataset: dict):
    # extract data
    work_id = dataset["id"].split("/")[-1]
    biblio = dataset["biblio"]

    # insert biblio
    if biblio and exists_work_id(conn, work_id):
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
    if referenced_works and exists_work_id(conn, work_id):
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
    if indexed_in and exists_work_id(conn, work_id):
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
    if keyword_ids_with_score and exists_work_id(conn, work_id):
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
    if topics and exists_work_id(conn, work_id):
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
    authors_with_institution_ids = []
    # extract data
    authors = []
    for authorship in dataset["authorships"]:
        institutions_ids = set()
        for institution in authorship["institutions"]:
            institutions_ids.add(institution["id"].split("/")[-1])
        authors.append(
            (
                (
                    authorship["author"]["id"].split("/")[-1]
                    if authorship["author"]["id"]
                    else None
                ),
                authorship["author"]["display_name"],
                authorship["author"]["orcid"],
                list(institutions_ids),
            )
        )

    # insert all authors if not already present
    if authors:
        sql_insert_author = """
            INSERT INTO author (openalex_id, display_name, orcid)
            VALUES (%s, %s, %s)
            RETURNING id;
        """
        sql_update_author_by_id = """
            UPDATE author
            SET openalex_id = COALESCE(%s, openalex_id),
                display_name = COALESCE(%s, display_name),
                orcid = COALESCE(%s, orcid) 
            WHERE id = %s
            RETURNING id;
        """
        with conn.cursor() as cur:
            for openalex_id, display_name, orcid, institution_ids in authors:
                if openalex_id or orcid:
                    # look for an existing row matching either identifier
                    cur.execute(
                        """
                            SELECT id FROM author
                            WHERE (%s IS NOT NULL AND openalex_id = %s)
                            OR (%s IS NOT NULL AND orcid = %s);
                        """,
                        (openalex_id, openalex_id, orcid, orcid),
                    )
                    existing = cur.fetchone()

                    if existing:
                        cur.execute(
                            sql_update_author_by_id,
                            (openalex_id, display_name, orcid, existing[0]),
                        )
                        author_id = cur.fetchone()[0]
                    else:
                        cur.execute(
                            sql_insert_author, (openalex_id, display_name, orcid)
                        )
                        author_id = cur.fetchone()[0]
                else:
                    # no openalex_id, no orcid -> try display_name + institution overlap first
                    author_id = get_author_id_by_display_name_and_institutions(
                        conn, display_name, institution_ids
                    )
                    if author_id is None:
                        # fall back to display_name only match if no institution overlap found
                        author_id = get_author_id_by_display_name(conn, display_name)
                    if author_id is None:
                        cur.execute(
                            sql_insert_author, (openalex_id, display_name, orcid)
                        )
                        author_id = cur.fetchone()[0]
                authors_with_institution_ids.append((author_id, institution_ids))
        conn.commit()

    return authors_with_institution_ids


def insert_author_country(conn: PgConnection, dataset: dict):
    # extract data
    author_counties = set()
    for authorship in dataset["authorships"]:
        author_id = get_author_id_by_orcid_and_openalex_id(
            conn,
            authorship["author"]["orcid"],
            (
                authorship["author"]["id"].split("/")[-1]
                if authorship["author"]["id"]
                else None
            ),
        )
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
                if author_country[0] is not None:
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
            ON CONFLICT (ror) DO NOTHING;
        """
        with conn.cursor() as cur:
            for (
                id,
                display_name,
                ror,
                institution_type_id,
                country_code_alpha_2,
            ) in institutions:
                if not exists_institution_id(conn, id):  # duplicate check
                    cur.execute(
                        sql,
                        (
                            id,
                            display_name,
                            ror,
                            institution_type_id,
                            country_code_alpha_2,
                        ),
                    )
        conn.commit()


def insert_work_author(
    conn: PgConnection, dataset: dict, authors_with_institution_ids: list
):
    # extract data
    work_id = dataset["id"].split("/")[-1]
    sql = """
        INSERT INTO work_author (work_id, author_id, author_position)
        VALUES (%s, %s, %s)
        ON CONFLICT (work_id, author_id) DO NOTHING;
    """
    with conn.cursor() as cur:
        for author_position, ai in enumerate(authors_with_institution_ids, start=1):
            if ai is not None:
                cur.execute(sql, (work_id, ai[0], author_position))
    conn.commit()


def insert_work_author_institution(
    conn: PgConnection, dataset: dict, authors_with_institution_ids: list
):
    # extract data
    work_id = dataset["id"].split("/")[-1]

    """'
    author_institutions = set()
    for authorship in dataset["authorships"]:
        author_id = get_author_id_by_orcid_and_openalex_id(
            conn,
            authorship["author"]["orcid"],
            (
                authorship["author"]["id"].split("/")[-1]
                if authorship["author"]["id"]
                else None
            ),
        )
        for institution in authorship["institutions"]:
            author_institutions.add((author_id, institution["id"].split("/")[-1]))
    """

    # insert work_author_institution if author_institutions is not emtpy
    # if author_institutions and exists_work_id(conn, work_id):
    sql = """
        INSERT INTO work_author_institution (work_id, author_id, institution_id)
        VALUES (%s, %s, %s)
        ON CONFLICT (work_id, author_id, institution_id) DO NOTHING;
    """
    with conn.cursor() as cur:
        for author_id, institution_ids in authors_with_institution_ids:
            for institution_id in institution_ids:
                cur.execute(sql, (work_id, author_id, institution_id))
    conn.commit()


def insert_funder(conn: PgConnection, dataset: dict):
    funder_ids = []
    # extract data
    funders = dataset["funders"]

    # insert all funders if not already present
    if funders:
        sql = """
            INSERT INTO funder (id, display_name, ror)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO UPDATE
                SET ror = COALESCE(openalex.funder.ror, EXCLUDED.ror)
            RETURNING id;
        """
        with conn.cursor() as cur:
            for funder in funders:
                id = funder["id"].split("/")[-1]
                ror = funder["ror"]
                existing_id = find_funder_by_ror(conn, ror)
                if existing_id:
                    funder_ids.append(existing_id)
                else:
                    cur.execute(
                        sql,
                        (
                            id,
                            funder["display_name"],
                            ror,
                        ),
                    )
                    funder_id = cur.fetchone()[0]
                    funder_ids.append(funder_id)
        conn.commit()
    return funder_ids


def insert_work_funder(conn: PgConnection, dataset: dict, funder_ids: list):
    # extract data
    work_id = dataset["id"].split("/")[-1]

    # insert work_funder if funders are present in dataset
    if funder_ids:
        sql = """
            INSERT INTO work_funder (work_id, funder_id)
            VALUES (%s, %s)
            ON CONFLICT (work_id, funder_id) DO NOTHING;
        """
        with conn.cursor() as cur:
            for funder_id in funder_ids:
                cur.execute(
                    sql,
                    (work_id, funder_id),
                )
        conn.commit()


def insert_work_award(conn: PgConnection, dataset: dict):
    # extract data
    work_id = dataset["id"]
    awards = dataset["awards"]

    # insert work_award if awards are present in dataset
    if awards and exists_work_id(conn, work_id):
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
                ON CONFLICT (issn_l) DO NOTHING;
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
                    if not exists_source_id(conn, id):  # duplicate check
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
                if source_id and exists_source_id(conn, source_id):
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
    if locations and exists_work_id(conn, work_id):
        locations[0] = (locations[0][0], True)  # set frist tuple as primary location
        sql = """
            INSERT INTO work_locations (work_id, locations_id, is_primary)
            VALUES (%s, %s, %s)
            ON CONFLICT (work_id, locations_id) DO NOTHING;
        """
        with conn.cursor() as cur:
            for locations_id, is_primary in locations:
                if exists_location_id(conn, locations_id):
                    cur.execute(sql, (work_id, locations_id, is_primary))
        conn.commit()
