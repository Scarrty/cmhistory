ALTER TABLE import_files
ADD COLUMN normalization_version INTEGER NOT NULL DEFAULT 1;
