\c openalex -- this line is needed for to use database in docker container, but will be skipped by load_sql_script function in db_manager.py 

CREATE SCHEMA IF NOT EXISTS openalex;

SET search_path TO openalex;

CREATE TABLE work_type (
    id VARCHAR PRIMARY KEY,
    display_description VARCHAR
);

CREATE TABLE languages (
    code_alpha_2_3 CHAR(3) PRIMARY KEY,
    display_name VARCHAR
);

CREATE TABLE work (
    id VARCHAR PRIMARY KEY,
    doi VARCHAR UNIQUE,
    type_id VARCHAR,
    title VARCHAR,
    publication_date TIMESTAMPTZ,
    publication_year INTEGER,
    language_code_alpha_2_3 CHAR(3),
    abstract_inverted_index JSONB,
    cited_by_count INTEGER,
    referenced_works_count INTEGER,
    authors_count INTEGER,
    locations_count INTEGER,
    is_open_access BOOLEAN,
    is_paratext BOOLEAN,
    is_retracted BOOLEAN,
    has_fulltext BOOLEAN,
    created_date TIMESTAMPTZ,
    updated_date TIMESTAMPTZ,

    CONSTRAINT fk_work_work_type 
        FOREIGN KEY (type_id) REFERENCES work_type (id),
    CONSTRAINT fk_work_language
        FOREIGN KEY (language_code_alpha_2_3) REFERENCES languages (code_alpha_2_3)
);

CREATE TABLE biblio (
    work_id VARCHAR PRIMARY KEY,
    volume VARCHAR,
    issue VARCHAR,
    first_page VARCHAR,
    last_page VARCHAR,

    CONSTRAINT fk_biblio_work
        FOREIGN KEY (work_id) REFERENCES work (id) ON DELETE CASCADE
);

CREATE TABLE work_reference (
    work_id VARCHAR,
    referenced_work_id VARCHAR,

    PRIMARY KEY (work_id, referenced_work_id),

    CONSTRAINT fk_work_reference_work
        FOREIGN KEY (work_id) REFERENCES work (id) ON DELETE CASCADE
);

CREATE TABLE indexed_in (
    id VARCHAR PRIMARY KEY,
    display_name VARCHAR
);

CREATE TABLE work_indexed_in (
    work_id VARCHAR,
    indexed_in_id VARCHAR,

    PRIMARY KEY (work_id, indexed_in_id),

    CONSTRAINT fk_work_indexed_in_work
        FOREIGN KEY (work_id) REFERENCES work (id) ON DELETE CASCADE,
    CONSTRAINT fk_work_indexed_in_index_in
        FOREIGN KEY (indexed_in_id) REFERENCES indexed_in (id)
);

CREATE TABLE keyword (
    id VARCHAR PRIMARY KEY,
    display_name VARCHAR
);

CREATE TABLE work_keyword (
    work_id VARCHAR,
    keyword_id VARCHAR,
    score DOUBLE PRECISION,

    PRIMARY KEY (work_id, keyword_id),

    CONSTRAINT fk_work_keyword_work
        FOREIGN KEY (work_id) REFERENCES work (id) ON DELETE CASCADE,
    CONSTRAINT fk_work_keyword_keyword
        FOREIGN KEY (keyword_id) REFERENCES keyword (id)
);

CREATE TABLE domain (
    id INTEGER PRIMARY KEY,
    display_name VARCHAR
);

CREATE TABLE field (
    id INTEGER PRIMARY KEY,
    domain_id INTEGER,
    display_name VARCHAR,

    CONSTRAINT fk_field_domain
        FOREIGN KEY (domain_id) REFERENCES domain (id)
);

CREATE TABLE subfield (
    id INTEGER PRIMARY KEY,
    field_id INTEGER,
    display_name VARCHAR,

    CONSTRAINT fk_subfield_field
        FOREIGN KEY (field_id) REFERENCES field (id)
);

CREATE TABLE topic (
    id VARCHAR PRIMARY KEY,
    subfield_id INTEGER,
    display_name VARCHAR,

    CONSTRAINT fk_topic_subfield
        FOREIGN KEY (subfield_id) REFERENCES subfield (id)
);

CREATE TABLE work_topic (
    work_id VARCHAR,
    topic_id VARCHAR,
    score DOUBLE PRECISION,

    PRIMARY KEY (work_id, topic_id),

    CONSTRAINT fk_work_topic_work
        FOREIGN KEY (work_id) REFERENCES work (id) ON DELETE CASCADE,
    CONSTRAINT fk_work_topic_topic
        FOREIGN KEY (topic_id) REFERENCES topic (id)
);

CREATE TABLE country (
    code_alpha_2 CHAR(2) PRIMARY KEY,
    display_name VARCHAR
);

CREATE TABLE author (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    openalex_id VARCHAR,
    display_name VARCHAR UNIQUE,
    orcid VARCHAR 
);

CREATE TABLE author_country (
    author_id INTEGER,
    country_code_alpha_2 CHAR(2),

    PRIMARY KEY (author_id, country_code_alpha_2),

    CONSTRAINT fk_author_country_author
        FOREIGN KEY (author_id) REFERENCES author (id),
    CONSTRAINT fk_author_country_country
        FOREIGN KEY (country_code_alpha_2) REFERENCES country (code_alpha_2)
);

CREATE TABLE institution_type (
    id VARCHAR PRIMARY KEY,
    display_name VARCHAR
);

CREATE TABLE institution (
    id VARCHAR PRIMARY KEY,
    display_name VARCHAR,
    ror VARCHAR UNIQUE,
    institution_type_id VARCHAR,
    country_code_alpha_2 CHAR(2),

    CONSTRAINT fk_institution_institution_type
        FOREIGN KEY (institution_type_id) REFERENCES institution_type (id),
    CONSTRAINT fk_institution_country
        FOREIGN KEY (country_code_alpha_2) REFERENCES country (code_alpha_2)
);

CREATE TABLE work_author (
    work_id VARCHAR,
    author_id INTEGER,
    author_position INTEGER,

    PRIMARY KEY (work_id, author_id),

    CONSTRAINT fk_work_author_work
        FOREIGN KEY (work_id) REFERENCES work (id) ON DELETE CASCADE,
    CONSTRAINT fk_work_author_author
        FOREIGN KEY (author_id) REFERENCES author (id)
);

CREATE TABLE work_author_institution (
    work_id VARCHAR,
    author_id INTEGER,
    institution_id VARCHAR,

    PRIMARY KEY (work_id, author_id, institution_id),

    CONSTRAINT fk_work_author_institution_work
        FOREIGN KEY (work_id) REFERENCES work (id) ON DELETE CASCADE,
    CONSTRAINT fk_work_author_institution_author
        FOREIGN KEY (author_id) REFERENCES author (id),
    CONSTRAINT fk_work_author_institution_institution
        FOREIGN KEY (institution_id) REFERENCES institution (id)
);

CREATE TABLE funder (
    id VARCHAR PRIMARY KEY,
    display_name VARCHAR,
    ror VARCHAR
);

CREATE TABLE work_funder (
    work_id VARCHAR REFERENCES work (id),
    funder_id VARCHAR REFERENCES funder (id),

    PRIMARY KEY (work_id, funder_id),

    CONSTRAINT fk_work_funder_work
        FOREIGN KEY (work_id) REFERENCES work (id) ON DELETE CASCADE,
    CONSTRAINT fk_work_funder_funder
        FOREIGN KEY (funder_id) REFERENCES funder (id)
);

CREATE TABLE work_award (
    work_id VARCHAR REFERENCES work (id),
    award_id VARCHAR,

    PRIMARY KEY (work_id, award_id),

    CONSTRAINT fk_work_award
        FOREIGN KEY (work_id) REFERENCES work (id) ON DELETE CASCADE
);

CREATE TABLE source_type (
    id VARCHAR PRIMARY KEY,
    display_name VARCHAR
);

CREATE TABLE source (
    id VARCHAR PRIMARY KEY,
    issn_l VARCHAR,
    display_name VARCHAR,
    host_organisation VARCHAR,
    host_organisation_name VARCHAR,
    source_type_id VARCHAR,
    is_open_access BOOLEAN,

    CONSTRAINT fk_source_source_type
        FOREIGN KEY (source_type_id) REFERENCES source_type (id)
);

CREATE TABLE versions (
    id VARCHAR PRIMARY KEY,
    display_description VARCHAR
);

CREATE TABLE license (
    id VARCHAR PRIMARY KEY,
    display_name VARCHAR
);

CREATE TABLE locations (
    id VARCHAR PRIMARY KEY,
    source_id VARCHAR,
    pdf_url VARCHAR,
    landing_page_url VARCHAR,
    version_id VARCHAR,
    license_id VARCHAR,
    is_open_access BOOLEAN,
    is_accepted BOOLEAN,
    is_published BOOLEAN,

    CONSTRAINT fk_locations_source
        FOREIGN KEY (source_id) REFERENCES source (id),
    CONSTRAINT fk_locations_versions
        FOREIGN KEY (version_id) REFERENCES versions (id),
    CONSTRAINT fk_locations_license
        FOREIGN KEY (license_id) REFERENCES license (id)
);

CREATE TABLE work_locations (
    work_id VARCHAR,
    locations_id VARCHAR,
    is_primary BOOLEAN,

    PRIMARY KEY (work_id, locations_id),

    CONSTRAINT fk_work_locations_work
        FOREIGN KEY (work_id) REFERENCES work (id) ON DELETE CASCADE,
    CONSTRAINT fk_work_locations_locations
        FOREIGN KEY (locations_id) REFERENCES locations (id) ON DELETE CASCADE
);