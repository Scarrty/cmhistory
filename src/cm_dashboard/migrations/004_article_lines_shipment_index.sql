BEGIN IMMEDIATE;

CREATE INDEX IF NOT EXISTS idx_article_lines_shipment_id
    ON article_lines(shipment_id);

INSERT OR IGNORE INTO schema_migrations (migration_id)
VALUES ('004_article_lines_shipment_index.sql');

COMMIT;
