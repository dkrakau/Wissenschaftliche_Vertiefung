\c arm_db

CREATE SCHEMA IF NOT EXISTS arm;

SET search_path TO arm, public;

CREATE TABLE arm.language (
    code_alpha2 CHAR(2) PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE arm.origin (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(150) NOT NULL UNIQUE
);

CREATE TABLE arm.discipline (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(150) NOT NULL UNIQUE
);

CREATE TABLE arm.license (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(150) NOT NULL UNIQUE,
    description VARCHAR(500)
);

CREATE TABLE arm.author (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    title VARCHAR(10),
    name VARCHAR(150) NOT NULL,
    orcid VARCHAR(19),

    CONSTRAINT chk_author_orcid_format
        CHECK (orcid IS NULL OR orcid ~ '^\d{4}-\d{4}-\d{4}-\d{3}[\dXx]$')
);

CREATE TABLE arm.source (
    issn VARCHAR(15) PRIMARY KEY,
    name VARCHAR(255),
    host_organisation VARCHAR(255),
    type VARCHAR(255)
);

CREATE TABLE arm.work (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    doi VARCHAR(255),
    title VARCHAR(500) NOT NULL,
    subtitle VARCHAR(500),
    abstract TEXT,
    keywords TEXT,
    publication TIMESTAMPTZ,
    cite INTEGER NOT NULL DEFAULT 0,
    public BOOLEAN NOT NULL DEFAULT TRUE,
    url VARCHAR(500),
    license_id INTEGER,
    issn VARCHAR(9),
    origin_id INTEGER,
    language_code_alpha2 CHAR(2),
    
    FOREIGN KEY (license_id) REFERENCES arm.license (id),
    FOREIGN KEY (issn) REFERENCES arm.source (issn),
    FOREIGN KEY (language_code_alpha2) REFERENCES arm.language (code_alpha2),

    CONSTRAINT chk_work_cite_non_negative CHECK (cite >= 0)
);

CREATE TABLE arm.work_author (
    work_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    FOREIGN KEY (work_id) REFERENCES arm.work (id),
    FOREIGN KEY (author_id) REFERENCES arm.author (id)
);

CREATE TABLE arm.work_discipline (
    work_id INTEGER NOT NULL,
    discipline_id INTEGER NOT NULL,
    FOREIGN KEY (work_id) REFERENCES arm.work (id),
    FOREIGN KEY (discipline_id) REFERENCES arm.discipline (id)
);