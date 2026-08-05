import psycopg2
from psycopg2.extensions import connection as PgConnection
from config import load_config
from connect import connect


def load_sql_script(file: str) -> str:
    with open(file, "r") as f:
        lines = f.readlines()
    return "".join(lines[1:])


def execute(conn: PgConnection, sql_script: str):
    print(sql_script)
    try:
        with conn.cursor() as cur:
            cur.execute(sql_script)
        conn.commit()
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)
        conn.rollback()
        raise


# template for create_table_ functions
def create_table_(conn: PgConnection):
    sql = """
        
    """
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)


def main():

    # load db config data
    config = load_config("database.ini")
    # connect to posgres db
    conn = connect(config)

    execute(conn, "DROP SCHEMA IF EXISTS openalex CASCADE;")
    execute(conn, load_sql_script("../postgres/scripts/create_schema.sql"))


if __name__ == "__main__":
    main()

# cd .\database\scripts
# python db_manager.py
