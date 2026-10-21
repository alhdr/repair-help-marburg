-- ============================================================
--  Marburg Repair Hub — database schema
-- ============================================================

DROP TABLE IF EXISTS cafe_services;
DROP TABLE IF EXISTS cafes;
DROP TABLE IF EXISTS services;
DROP TABLE IF EXISTS faqs;
DROP TABLE IF EXISTS settings;
DROP TABLE IF EXISTS messages;

-- Key/value site settings (e.g. the Contact-form receiver email)
CREATE TABLE settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Services a cafe can offer (the categories shown on the home page)
CREATE TABLE services (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    slug     TEXT UNIQUE NOT NULL,   -- maps to a CSS background class
    name_en  TEXT NOT NULL,
    name_de  TEXT NOT NULL,
    icon     TEXT NOT NULL DEFAULT '',
    featured INTEGER NOT NULL DEFAULT 0  -- 1 = show as a category card
);

-- Repair locations
CREATE TABLE cafes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    address       TEXT DEFAULT '',
    hours         TEXT DEFAULT '',
    pricing       TEXT DEFAULT '',
    accessibility TEXT DEFAULT '',
    notes         TEXT DEFAULT '',
    website       TEXT DEFAULT '',
    lat           REAL,
    lng           REAL
);

-- Many-to-many: a cafe can offer multiple services
CREATE TABLE cafe_services (
    cafe_id    INTEGER NOT NULL REFERENCES cafes(id)    ON DELETE CASCADE,
    service_id INTEGER NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    PRIMARY KEY (cafe_id, service_id)
);

-- FAQ entries (bilingual)
CREATE TABLE faqs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    question_en TEXT NOT NULL,
    answer_en   TEXT NOT NULL,
    question_de TEXT NOT NULL DEFAULT '',
    answer_de   TEXT NOT NULL DEFAULT '',
    position    INTEGER NOT NULL DEFAULT 0
);

-- Contact-form submissions
CREATE TABLE messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT,
    email      TEXT,
    subject    TEXT,
    body       TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
