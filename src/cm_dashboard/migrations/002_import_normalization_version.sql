BEGIN IMMEDIATE;

ALTER TABLE import_files
ADD COLUMN normalization_version INTEGER NOT NULL DEFAULT 1;

INSERT OR IGNORE INTO schema_migrations (migration_id)
VALUES ('002_import_normalization_version.sql');

COMMIT;
