from psycopg2.extensions import connection as PgConnection


def insert_work_type(conn: PgConnection, dataset: dict, work_types: dict):
    # extract data
    work_type_id = dataset["type"]
    # insert work_type if not already present
    sql = """
        INSERT INTO work_type (id, display_description)
        VALUES (%s, %s)
        ON CONFLICT (id) DO NOTHING;
    """
    with conn.cursor() as cur:
        display_description = work_types.get(work_type_id)
        cur.execute(sql, (work_type_id, display_description))
    conn.commit()


def insert_languages(conn: PgConnection, dataset: dict, language_types: dict):
    # extract data
    code_alpha2 = dataset["language"]
    # insert languages if not already present
    sql = """
        INSERT INTO languages (code_alpha2, display_name)
        VALUES (%s, %s)
        ON CONFLICT (id) DO NOTHING;;
    """
    with conn.cursor() as cur:
        display_name = language_types.get(code_alpha2)
        cur.execute(sql, (code_alpha2, display_name))
    conn.commit()


def insert_work(conn: PgConnection, dataset: dict):
    # extract data
    work_id = dataset["id"].split("/")[-1]
    doi = dataset["doi"]
    type_id = dataset["type"]
    title = dataset["title"]
    publication_date = dataset["publication_date"]  # parse to timestampz?
    publication_year = int(dataset["publication_year"])
    language_code_alpha2 = dataset["language"]
    abstract_inverted_index = dataset["abstract_inverted_index"]
    cited_by_count = int(dataset["cited_by_count"])
    referenced_works_count = int(dataset["referenced_works_count"])
    authors_count = int(dataset["authors_count"])
    locations_count = int(dataset["locations_count"])
    is_open_access = bool(dataset["open_access"]["is_oa"])
    is_paratext = bool(dataset["is_paratext"])
    is_retracted = bool(dataset["is_retracted"])
    has_fulltext = bool(dataset["has_fulltext"])
    created_date = dataset["created_date"]  # parse to timestampz?
    updated_date = dataset["updated_date"]  # parse to timestampz?
    # insert work
    sql = """
        INSERT INTO work (
            id,
            doi,
            type_id,
            title,
            publication_date,
            publication_year,
            language_code_alpha2,
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
                publication_year,
                language_code_alpha2,
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
    # insert work_reference
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
    # insert indexed_in if not already present
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
    # insert work_indexed_in
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
    # insert keyword if not already present
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
    # insert work_keyword
    sql = """
        INSERT INTO work_keyword (work_id, keyword_id, score)
        VALUES (%s, %s, %s);
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
    # insert domain if not already present
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
    # insert field if not already present
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
    # insert subfield if not already present
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
    # insert topic if not already present
    sql = """
        INSERT INTO subfield (id, subfield_id, display_name)
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
    # insert work_topic
    sql = """
        INSERT INTO work_topic (work_id, topic_id, score)
        VALUES (%s, %s, %s);
    """
    with conn.cursor() as cur:
        for topic_id, score in topics:
            cur.execute(sql, (work_id, topic_id, score))
    conn.commit()


def insert_country(conn: PgConnection, dataset: dict, country_types: dict):
    print("insert_country")


def insert_author(conn: PgConnection, dataset: dict):
    print("insert_author")


def insert_author_country(conn: PgConnection, dataset: dict):
    print("insert_author_country")


def insert_institution_type(conn: PgConnection, dataset: dict, institute_types: dict):
    print("insert_institute_type")


def insert_institution(conn: PgConnection, dataset: dict):
    print("insert_institution")


def insert_work_author(conn: PgConnection, dataset: dict):
    # extract data
    work_id = dataset["id"].split("/")[-1]
    print("insert_work_author")


def insert_work_author_institution(conn: PgConnection, dataset: dict):
    # extract data
    work_id = dataset["id"].split("/")[-1]
    print("insert_work_author_institution")


def insert_funder(conn: PgConnection, dataset: dict):
    print("insert_funder")


def insert_work_funder(conn: PgConnection, dataset: dict):
    # extract data
    work_id = dataset["id"].split("/")[-1]
    print("insert_work_funder")


def insert_work_award(conn: PgConnection, dataset: dict):
    # extract data
    work_id = dataset["id"].split("/")[-1]
    print("insert_work_award")


def insert_source_type(conn: PgConnection, dataset: dict, source_types: dict):
    print("insert_source_type")


def insert_source(conn: PgConnection, dataset: dict):
    print("insert_source")


def insert_versions(conn: PgConnection, dataset: dict, version_types: dict):
    print("insert_versions")


def insert_license(conn: PgConnection, dataset: dict, license_types: dict):
    print("insert_license")


def insert_locations(conn: PgConnection, dataset: dict):
    print("insert_locations")


def insert_work_locations(conn: PgConnection, dataset: dict):
    # extract data
    work_id = dataset["id"].split("/")[-1]
    print("insert_work_locations")
