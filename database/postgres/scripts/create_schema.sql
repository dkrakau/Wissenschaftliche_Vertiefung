\c openalex

CREATE SCHEMA IF NOT EXISTS openalex;

SET search_path TO openalex;

CREATE TABLE work_type (
    id VARCHAR PRIMARY KEY,
    display_description VARCHAR
);

CREATE TABLE languages (
    code_alpha2 CHAR(2) PRIMARY KEY,
    display_name VARCHAR
);

CREATE TABLE work (
    id VARCHAR PRIMARY KEY,
    doi VARCHAR UNIQUE,
    type_id VARCHAR,
    title VARCHAR,
    publication_date TIMESTAMPTZ,
    publication_year INTEGER,
    language_code_alpha2 CHAR(2),
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
        FOREIGN KEY (language_code_alpha2) REFERENCES languages (code_alpha2)
);

CREATE TABLE biblio (
    work_id VARCHAR PRIMARY KEY REFERENCES work (id),
    volume VARCHAR,
    issue VARCHAR,
    first_page VARCHAR,
    last_page VARCHAR
);

CREATE TABLE work_reference (
    work_id VARCHAR REFERENCES work (id),
    referenced_work_id VARCHAR,

    PRIMARY KEY (work_id, referenced_work_id)
);

CREATE TABLE indexed_in (
    id VARCHAR PRIMARY KEY,
    display_name VARCHAR
);

CREATE TABLE work_indexed_in (
    work_id VARCHAR REFERENCES work (id),
    indexed_in_id VARCHAR REFERENCES indexed_in (id),

    PRIMARY KEY (work_id, indexed_in_id)
);

CREATE TABLE keyword (
    id VARCHAR PRIMARY KEY,
    display_name VARCHAR
);

CREATE TABLE work_keyword (
    work_id VARCHAR REFERENCES work (id),
    keyword_id VARCHAR REFERENCES keyword (id),
    score DOUBLE PRECISION,

    PRIMARY KEY (work_id, keyword_id)
);

CREATE TABLE domain (
    id INTEGER PRIMARY KEY,
    display_name VARCHAR
);

CREATE TABLE field (
    id INTEGER PRIMARY KEY,
    domain_id INTEGER REFERENCES domain (id),
    display_name VARCHAR
);

CREATE TABLE subfield (
    id INTEGER PRIMARY KEY,
    field_id INTEGER REFERENCES field (id),
    display_name VARCHAR
);

CREATE TABLE topic (
    id VARCHAR PRIMARY KEY,
    subfield_id INTEGER REFERENCES subfield (id),
    display_name VARCHAR
);

CREATE TABLE work_topic (
    work_id VARCHAR REFERENCES work (id),
    topic_id VARCHAR REFERENCES topic (id),
    score DOUBLE PRECISION,

    PRIMARY KEY (work_id, topic_id)
);

CREATE TABLE country (
    code_alpha2 CHAR(2) PRIMARY KEY,
    display_name VARCHAR
);

CREATE TABLE author (
    id VARCHAR PRIMARY KEY,
    display_name VARCHAR,
    orcid VARCHAR UNIQUE
);

CREATE TABLE author_country (
    author_id VARCHAR REFERENCES author (id),
    country_code_alpha2 CHAR(2) REFERENCES country (code_alpha2),

    PRIMARY KEY (author_id, country_code_alpha2)
);

CREATE TABLE institution_type (
    id VARCHAR PRIMARY KEY,
    display_name VARCHAR
);

CREATE TABLE institution (
    id VARCHAR PRIMARY KEY,
    display_name VARCHAR,
    ror VARCHAR UNIQUE,
    institution_type_id VARCHAR REFERENCES institution_type (id),
    country_code_alpha2 CHAR(2) REFERENCES country (code_alpha2)
);

CREATE TABLE work_author (
    work_id VARCHAR REFERENCES work (id),
    author_id VARCHAR REFERENCES author (id),
    author_position INTEGER,

    PRIMARY KEY (work_id, author_id)
);

CREATE TABLE work_author_institution (
    work_id VARCHAR REFERENCES work (id),
    author_id VARCHAR REFERENCES author (id),
    institution_id VARCHAR REFERENCES institution (id),

    PRIMARY KEY (work_id, author_id, institution_id)
);

CREATE TABLE funder (
    id VARCHAR PRIMARY KEY,
    display_name VARCHAR,
    ror VARCHAR UNIQUE
);

CREATE TABLE work_funder (
    work_id VARCHAR REFERENCES work (id),
    funder_id VARCHAR REFERENCES funder (id),

    PRIMARY KEY (work_id, funder_id)
);

CREATE TABLE work_award (
    work_id VARCHAR REFERENCES work (id),
    award_id VARCHAR,

    PRIMARY KEY (work_id, award_id)
);

CREATE TABLE source_type (
    id VARCHAR PRIMARY KEY,
    display_name VARCHAR
);

CREATE TABLE source (
    id VARCHAR PRIMARY KEY,
    issn_l VARCHAR UNIQUE,
    display_name VARCHAR,
    host_organisation VARCHAR,
    host_organisation_name VARCHAR,
    source_type_id VARCHAR REFERENCES source_type (id),
    is_open_access BOOLEAN
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
    source_id VARCHAR REFERENCES source (id),
    pdf_url VARCHAR,
    landing_page_url VARCHAR,
    version_id VARCHAR REFERENCES versions (id),
    license_id VARCHAR REFERENCES license (id),
    is_open_access BOOLEAN,
    is_accepted BOOLEAN,
    is_published BOOLEAN
);

CREATE TABLE work_locations (
    work_id VARCHAR REFERENCES work (id),
    locations_id VARCHAR REFERENCES locations (id),
    is_primary BOOLEAN,

    PRIMARY KEY (work_id, locations_id)
);