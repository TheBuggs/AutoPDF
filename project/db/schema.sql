DROP TABLE IF EXISTS records;

CREATE TABLE records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fid TEXT NULL,
    tid TEXT NOT NULL,
    token TEXT NOT NULL,
    fname TEXT NULL,
    fext TEXT NULL,
    active INT NULL
);