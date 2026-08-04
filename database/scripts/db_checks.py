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