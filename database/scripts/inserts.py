from psycopg2.extensions import connection as PgConnection

def has_work_type(conn: PgConnection, work_type_id: str):
    sql = "SELECT EXISTS(SELECT 1 FROM work_type WHERE id = %s);"
    with conn.cursor() as cur:
        cur.execute(sql, (work_type_id,))
        return cur.fetchone()[0]

def has_language(conn: PgConnection, code_alpha2: str):
    sql = "SELECT EXISTS(SELECT 1 FROM languages WHERE code_alpha2 = %s);"
    with conn.cursor() as cur:
        cur.execute(sql, (code_alpha2,))
        return cur.fetchone()[0]

def has_work(conn: PgConnection, work_id: str):
    sql = "SELECT EXISTS(SELECT 1 FROM work WHERE id = %s);"
    with conn.cursor() as cur:
        cur.execute(sql, (work_id,))
        return cur.fetchone()[0]

def has_indexed_in(conn: PgConnection, indexed_in_id: str):
    sql = "SELECT EXISTS(SELECT 1 FROM indexed_in WHERE id = %s);"
    with conn.cursor() as cur:
        cur.execute(sql, (indexed_in_id,))
        return cur.fetchone()[0]

def has_keyword(conn: PgConnection, keyword: str):
    sql = "SELECT EXISTS(SELECT 1 FROM keyword WHERE keyword = %s);"
    with conn.cursor() as cur:
        cur.execute(sql, (keyword,))
        return cur.fetchone()[0]

def has_domain(conn: PgConnection, domain_id: str):
    sql = "SELECT EXISTS(SELECT 1 FROM domain WHERE id = %s);"
    with conn.cursor() as cur:
        cur.execute(sql, (domain_id,))
        return cur.fetchone()[0]

def has_field(conn: PgConnection, field_id: str):
    sql = "SELECT EXISTS(SELECT 1 FROM field WHERE id = %s);"
    with conn.cursor() as cur:
        cur.execute(sql, (field_id,))
        return cur.fetchone()[0]

def has_subfield(conn: PgConnection, subfield_id: str):
    sql = "SELECT EXISTS(SELECT 1 FROM subfield WHERE id = %s);"
    with conn.cursor() as cur:
        cur.execute(sql, (subfield_id,))
        return cur.fetchone()[0]

def has_topic(conn: PgConnection, topic_id: str):
    sql = "SELECT EXISTS(SELECT 1 FROM topic WHERE id = %s);"
    with conn.cursor() as cur:
        cur.execute(sql, (topic_id,))
        return cur.fetchone()[0]

def has_country(conn: PgConnection, code_alpha2: str):
    sql = "SELECT EXISTS(SELECT 1 FROM country WHERE code_alpha2 = %s);"
    with conn.cursor() as cur:
        cur.execute(sql, (code_alpha2,))
        return cur.fetchone()[0]

def has_author(conn: PgConnection, author_id: str):
    sql = "SELECT EXISTS(SELECT 1 FROM author WHERE id = %s);"
    with conn.cursor() as cur:
        cur.execute(sql, (author_id,))
        return cur.fetchone()[0]

def has_institution_type(conn: PgConnection, institution_type_id: str):
    sql = "SELECT EXISTS(SELECT 1 FROM institution_type WHERE id = %s);"
    with conn.cursor() as cur:
        cur.execute(sql, (institution_type_id,))
        return cur.fetchone()[0]

def has_institution(conn: PgConnection, institution_id: str):
    sql = "SELECT EXISTS(SELECT 1 FROM institution WHERE id = %s);"
    with conn.cursor() as cur:
        cur.execute(sql, (institution_id,))
        return cur.fetchone()[0]

def has_funder(conn: PgConnection, funder_id: str):
    sql = "SELECT EXISTS(SELECT 1 FROM funder WHERE id = %s);"
    with conn.cursor() as cur:
        cur.execute(sql, (funder_id,))
        return cur.fetchone()[0]

def has_source_type(conn: PgConnection, source_typ_id: str):
    sql = "SELECT EXISTS(SELECT 1 FROM source_type_id WHERE id = %s);"
    with conn.cursor() as cur:
        cur.execute(sql, (source_typ_id,))
        return cur.fetchone()[0]

def has_source(conn: PgConnection, source_id: str):
    sql = "SELECT EXISTS(SELECT 1 FROM source WHERE id = %s);"
    with conn.cursor() as cur:
        cur.execute(sql, (source_id,))
        return cur.fetchone()[0]

def has_version(conn: PgConnection, version_id: str):
    sql = "SELECT EXISTS(SELECT 1 FROM version WHERE id = %s);"
    with conn.cursor() as cur:
        cur.execute(sql, (version_id,))
        return cur.fetchone()[0]

def has_license(conn: PgConnection, license_id: str):
    sql = "SELECT EXISTS(SELECT 1 FROM license WHERE id = %s);"
    with conn.cursor() as cur:
        cur.execute(sql, (license_id,))
        return cur.fetchone()[0]

def has_location(conn: PgConnection, locatoin_id: str):
    sql = "SELECT EXISTS(SELECT 1 FROM locations WHERE id = %s);"
    with conn.cursor() as cur:
        cur.execute(sql, (locatoin_id,))
        return cur.fetchone()[0]
    

def insert_work_type(conn: PgConnection, dataset: dict, work_types: dict):
    # extract neccessary data from openalex work dataset
    work_type_id = dataset["type"]
    display_description = None
    # verify that value is present in types
    if work_type_id in work_types:
        display_description = work_types[work_type_id]
    # insert values if not already present
    if not has_work_type(conn, work_type_id):
        sql = """INSERT INTO work_type (id, display_description) VALUES (%s, %s);"""
        with conn.cursor() as cur:
            cur.execute(sql, (work_type_id, display_description))
        conn.commit()

def insert_languages(conn: PgConnection, dataset: dict, language_types: dict):
    # extract neccessary data from openalex work dataset
    code_alpha2 = dataset["language"]
    display_name = None
    # verify that value is present in types
    if code_alpha2 in language_types:
        display_name = language_types[code_alpha2]
    # insert values if not already present
    if not has_work_type(conn, code_alpha2):
        sql = """INSERT INTO languages (code_alpha2, display_name) VALUES (%s, %s);"""
        with conn.cursor() as cur:
            cur.execute(sql, (code_alpha2, display_name))
        conn.commit()

def insert_work(conn: PgConnection, dataset: dict):
    print("insert_work")

def insert_biblio(conn: PgConnection, dataset: dict):
    print("insert_biblio")

def insert_work_reference(conn: PgConnection, dataset: dict):
    print("insert_work_reference")

def insert_indexed_in(conn: PgConnection, dataset: dict, indexed_in_types: dict):
    print("insert_indexed_in")

def insert_work_indexed_in(conn: PgConnection, dataset: dict):
    print("insert_work_indexed_in")

def insert_keyword(conn: PgConnection, dataset: dict):
    print("insert_keyword")

def insert_work_keyword(conn: PgConnection, dataset: dict):
    print("insert_work_keyword")

def insert_domain(conn: PgConnection, dataset: dict):
    print("insert_domain")

def insert_field(conn: PgConnection, dataset: dict):
    print("insert_field")

def insert_subfield(conn: PgConnection, dataset: dict):
    print("insert_subfield")

def insert_topic(conn: PgConnection, dataset: dict):
    print("insert_topic")

def insert_work_topic(conn: PgConnection, dataset: dict):
    print("insert_work_topic")

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
    print("insert_work_author")

def insert_work_author_institution(conn: PgConnection, dataset: dict):
    print("insert_work_author_institution")

def insert_funder(conn: PgConnection, dataset: dict):
    print("insert_funder")

def insert_work_funder(conn: PgConnection, dataset: dict):
    print("insert_work_funder")

def insert_work_award(conn: PgConnection, dataset: dict):
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
    print("insert_work_locations")