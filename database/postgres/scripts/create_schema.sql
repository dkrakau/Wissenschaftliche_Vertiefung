\c arm_db

CREATE SCHEMA IF NOT EXISTS arm;

SET search_path TO arm, public;

CREATE TABLE arm.language (
    code_alpha2 CHAR(2) NOT NULL,
    name VARCHAR(100) NOT NULL,
    CONSTRAINT pk_language PRIMARY KEY (code_alpha2)
);

CREATE TABLE arm.origin (
    id INTEGER GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(150) NOT NULL,
    CONSTRAINT pk_origin PRIMARY KEY (id)
    CONSTRAINT uq_origin_name UNIQUE (name)
);

CREATE TABLE arm.discipline (
    id INTEGER GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(150) NOT NULL,
    CONSTRAINT pk_discipline PRIMARY KEY (id),
    CONSTRAINT uq_discipline_name UNIQUE (name)
);

CREATE TABLE arm.license (
    id INTEGER GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(150) NOT NULL,
    description VARCHAR(500),
    CONSTRAINT pk_license PRIMARY KEY (id),
    CONSTRAINT uq_license_name UNIQUE (name)
);

CREATE TABLE arm.source (
    id INTEGER GENERATED ALWAYS AS IDENTITY,
    title VARCHAR(50),
    name VARCHAR(200) NOT NULL,
    orcid VARCHAR(19),
    CONSTRAINT pk_author PRIMARY KEY (id),
    CONSTRAINT uq_author_orcid UNIQUE (orcid),
    CONSTRAINT chk_author_orcid_format
        CHECK (orcid IS NULL OR orcid ~ '^\d{4}-\d{4}-\d{4}-\d{3}[\dXx]$')
);

CREATE TABLE arm.work (
    id INTEGER GENERATED ALWAYS AS IDENTITY,
    doi VARCHAR(255),
    title VARCHAR(500) NOT NULL,
    subtitle VARCAHR(500),
    abstract TEXT,
    keywords TEXT,
    publication TIMESTAMPTZ,
    cite INTEGER NOT NULL DEFAULT 0,
    public BOOLEAN NOT NULL DEFAULT TURE,
    url VARCHAR(500),
    license_id INTEGER,
    issn VARCHAR(9),
    origin_id INTEGER,
    language_code_alpha2 CHAR(2),

    CONSTRAINT pk_work PRIMARY KEY (id),
    CONSTRAINT uq_work_doi UNIQUE (doi),
    CONSTRAINT chk_work_cite_non_negative CECK (cite >= 0),
    
    CONSTRAINT fk_work_license
        FOREIGN KEY (license_id) REFERENCES arm.license (id)
        ON UPDATE CASCADE ON DELETE SET NULL,

    CONSTRAINT fk_work_source
        FOREIGN KEY (issn) REFERENCES arm.source (issn)
        ON UPDATE CASCADE DELETE SET NULL,
    
    CONSTRAINT fk_work_language
        FOREIGN KEY (language_code_alpha2) REFERENCES arm.language (code_alpha2)
        ON UPDATE CASCADE DLEETE SET NULL
);

CREATE TABLE arm.work_author (
    work_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,

    CONSTRAINT pk_work_author PRIMARY KEY (work_id, author_id),

    CONSTRAINT fk_work_author_work
        FOREIGN KEY (work_id) REFERENCES arm.work (id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    
    CONSTRAINT fk_work_author_author
        FOREIGN KEY (author_id) REFERENCES arm.author (id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE arm.work_discipline (
    work_id INTEGER NOT NULL,
    discipline_id INTEGER NOT NULL,

    CONSTRAINT pk_work_discipline PRIMARY KEY (work_id, discipline_id),

    CONSTRAINT fk_work_discipline_work
        FOREIGN KEY (work_id) REFERENCES arm.work (id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    
    CONSTRAINT fk_work_discipline_discipline
        FOREIGN KEY (discipline_id) REFERENCES arm.discipline (id)
        ON UPDATE CASCADE ON DELETE CASCADE
);