PRAGMA foreign_keys = OFF;

BEGIN IMMEDIATE;

CREATE TABLE shipments_v2 (
    shipment_id INTEGER PRIMARY KEY,
    order_id TEXT NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('PURCHASED', 'SOLD')),
    username TEXT,
    counterparty_name TEXT,
    street TEXT,
    city TEXT,
    country TEXT,
    is_professional INTEGER,
    vat_id_present INTEGER,
    article_count INTEGER,
    merchandise_value TEXT,
    shipment_costs TEXT,
    trustee_service_fee TEXT,
    commission TEXT,
    total_value TEXT,
    currency TEXT,
    UNIQUE (direction, order_id)
);

INSERT INTO shipments_v2 SELECT * FROM shipments;

CREATE TABLE shipment_events_v2 (
    shipment_event_id INTEGER PRIMARY KEY,
    shipment_id INTEGER NOT NULL REFERENCES shipments_v2(shipment_id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    event_datetime TEXT NOT NULL,
    source_import_file_id INTEGER REFERENCES import_files(import_file_id) ON DELETE SET NULL,
    UNIQUE (shipment_id, event_type, event_datetime)
);

INSERT INTO shipment_events_v2 SELECT * FROM shipment_events;

CREATE TABLE article_lines_v2 (
    article_line_id INTEGER PRIMARY KEY,
    shipment_id INTEGER REFERENCES shipments_v2(shipment_id) ON DELETE SET NULL,
    order_id TEXT NOT NULL,
    direction TEXT NOT NULL,
    date_basis TEXT NOT NULL,
    event_datetime TEXT NOT NULL,
    article_name_snapshot TEXT NOT NULL,
    product_id TEXT REFERENCES products(product_id) ON DELETE SET NULL,
    localized_product_name TEXT,
    expansion_id INTEGER REFERENCES expansions(expansion_id) ON DELETE SET NULL,
    expansion_name_snapshot TEXT,
    category_id INTEGER REFERENCES categories(category_id) ON DELETE SET NULL,
    category_name_snapshot TEXT,
    quantity INTEGER NOT NULL,
    article_value TEXT NOT NULL,
    total TEXT NOT NULL,
    currency TEXT NOT NULL,
    comments TEXT,
    source_import_file_id INTEGER REFERENCES import_files(import_file_id) ON DELETE SET NULL,
    source_row_number INTEGER,
    business_key TEXT NOT NULL UNIQUE
);

INSERT INTO article_lines_v2 SELECT * FROM article_lines;

DROP TABLE article_lines;
DROP TABLE shipment_events;
DROP TABLE shipments;

ALTER TABLE shipments_v2 RENAME TO shipments;
ALTER TABLE shipment_events_v2 RENAME TO shipment_events;
ALTER TABLE article_lines_v2 RENAME TO article_lines;

CREATE INDEX idx_shipments_direction_country
    ON shipments(direction, country);

CREATE INDEX idx_shipment_events_type_datetime
    ON shipment_events(event_type, event_datetime);

CREATE INDEX idx_article_lines_filters
    ON article_lines(direction, date_basis, event_datetime, product_id, order_id);

CREATE INDEX idx_article_lines_order_id
    ON article_lines(order_id);

COMMIT;

PRAGMA foreign_keys = ON;
