from pathlib import Path
import pandas as pd

from scripts.config import load_config
from scripts.connect import connect

DB_CONFIG = "scripts/database.ini"

CSV_DIR = Path("csv")
CSV_DIR.mkdir(exist_ok=True)

QUERY_OPEN_ACCESS = """
    WITH abstract_text AS (
    SELECT w.id, openalex.reconstruct_abstract(w.abstract_inverted_index) AS abstract_plain
    FROM openalex.work w
)
SELECT DISTINCT ON (w.id) w.id, w.doi, l.pdf_url, l.is_open_access, wl.is_primary
FROM openalex.work w
JOIN abstract_text at ON at.id = w.id
LEFT JOIN openalex.work_locations wl ON wl.work_id = w.id
LEFT JOIN openalex.locations l ON l.id = wl.locations_id AND l.pdf_url IS NOT NULL
WHERE w.type_id IN ('article')
  AND COALESCE(w.is_paratext, false) = false
  AND COALESCE(w.is_retracted, false) = false
  AND COALESCE(w.is_open_access, true) = true
  AND w.language_code_alpha_2_3 IN ('en', 'eng', 'de', 'deu')
  AND to_tsvector('english', COALESCE(w.title, '') || ' ' || COALESCE(at.abstract_plain, ''))
      @@ to_tsquery('english',
          'vector <-> database | vector <-> db | vektor <-> db '
          '| vectordatabase | vectordb | vektordatenbank '
          '| vector <-> store | vector <-> index | vector <-> search '
          '| embedding <-> database | embedding <-> store '
          '| ann <-> search | approximate <-> nearest <-> neighbor')
ORDER BY w.id, wl.is_primary DESC NULLS LAST;
"""

QUERY_NOT_OPEN_ACCESS = """
    WITH abstract_text AS (
    SELECT w.id, openalex.reconstruct_abstract(w.abstract_inverted_index) AS abstract_plain
    FROM openalex.work w
)
SELECT DISTINCT ON (w.id) w.id, w.doi, l.pdf_url, l.is_open_access, wl.is_primary
FROM openalex.work w
JOIN abstract_text at ON at.id = w.id
LEFT JOIN openalex.work_locations wl ON wl.work_id = w.id
LEFT JOIN openalex.locations l ON l.id = wl.locations_id AND l.pdf_url IS NOT NULL
WHERE w.type_id IN ('article')
  AND COALESCE(w.is_paratext, false) = false
  AND COALESCE(w.is_retracted, false) = false
  AND COALESCE(w.is_open_access, false) = false
  AND w.language_code_alpha_2_3 IN ('en', 'eng', 'de', 'deu')
  AND to_tsvector('english', COALESCE(w.title, '') || ' ' || COALESCE(at.abstract_plain, ''))
      @@ to_tsquery('english',
          'vector <-> database | vector <-> db | vektor <-> db '
          '| vectordatabase | vectordb | vektordatenbank '
          '| vector <-> store | vector <-> index | vector <-> search '
          '| embedding <-> database | embedding <-> store '
          '| ann <-> search | approximate <-> nearest <-> neighbor')
ORDER BY w.id, wl.is_primary DESC NULLS LAST;
"""


def main():
    # load db config data
    config = load_config(DB_CONFIG)
    # connect to posgres db
    conn = connect(config)

    df_open_access = pd.read_sql(QUERY_OPEN_ACCESS, conn)
    df_open_access.to_csv(CSV_DIR / "open_access.csv", index=False, encoding="utf-8")

    df_not_open_access = pd.read_sql(QUERY_NOT_OPEN_ACCESS, conn)
    df_not_open_access.to_csv(
        CSV_DIR / "not_open_access.csv", index=False, encoding="utf-8"
    )


if __name__ == "__main__":
    main()

# cd database
# python exporter.py
