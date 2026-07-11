CREATE TABLE IF NOT EXISTS import_files (
    import_file_id INTEGER PRIMARY KEY,
    original_path TEXT NOT NULL UNIQUE,
    file_name TEXT NOT NULL,
    file_hash TEXT,
    file_extension TEXT NOT NULL,
    direction TEXT NOT NULL,
    entity TEXT NOT NULL,
    date_basis TEXT NOT NULL,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    sheet_name TEXT,
    import_status TEXT NOT NULL DEFAULT 'pending',
    row_count INTEGER NOT NULL DEFAULT 0,
    imported_at TEXT
);

CREATE TABLE IF NOT EXISTS raw_article_rows (
    raw_article_row_id INTEGER PRIMARY KEY,
    import_file_id INTEGER NOT NULL REFERENCES import_files(import_file_id) ON DELETE CASCADE,
    source_row_number INTEGER NOT NULL,
    order_id TEXT,
    business_key TEXT,
    raw_values_json TEXT NOT NULL,
    UNIQUE (import_file_id, source_row_number)
);

CREATE TABLE IF NOT EXISTS raw_shipment_rows (
    raw_shipment_row_id INTEGER PRIMARY KEY,
    import_file_id INTEGER NOT NULL REFERENCES import_files(import_file_id) ON DELETE CASCADE,
    source_row_number INTEGER NOT NULL,
    order_id TEXT,
    resolved_order_id TEXT,
    is_header_row INTEGER NOT NULL,
    raw_values_json TEXT NOT NULL,
    inherited_values_json TEXT NOT NULL,
    UNIQUE (import_file_id, source_row_number)
);

CREATE TABLE IF NOT EXISTS shipments (
    shipment_id INTEGER PRIMARY KEY,
    order_id TEXT NOT NULL UNIQUE,
    direction TEXT NOT NULL,
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
    currency TEXT
);

CREATE TABLE IF NOT EXISTS shipment_events (
    shipment_event_id INTEGER PRIMARY KEY,
    shipment_id INTEGER NOT NULL REFERENCES shipments(shipment_id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    event_datetime TEXT NOT NULL,
    source_import_file_id INTEGER REFERENCES import_files(import_file_id) ON DELETE SET NULL,
    UNIQUE (shipment_id, event_type, event_datetime)
);

CREATE TABLE IF NOT EXISTS products (
    product_id TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS product_labels (
    product_label_id INTEGER PRIMARY KEY,
    product_id TEXT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    source_import_file_id INTEGER REFERENCES import_files(import_file_id) ON DELETE SET NULL,
    UNIQUE (product_id, label)
);

CREATE TABLE IF NOT EXISTS expansions (
    expansion_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS categories (
    category_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS article_lines (
    article_line_id INTEGER PRIMARY KEY,
    shipment_id INTEGER REFERENCES shipments(shipment_id) ON DELETE SET NULL,
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

CREATE TABLE IF NOT EXISTS import_issues (
    import_issue_id INTEGER PRIMARY KEY,
    import_file_id INTEGER REFERENCES import_files(import_file_id) ON DELETE CASCADE,
    severity TEXT NOT NULL,
    code TEXT NOT NULL,
    message TEXT NOT NULL,
    source_row_number INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_import_files_context
    ON import_files(direction, entity, date_basis, period_start, period_end);

CREATE INDEX IF NOT EXISTS idx_raw_article_rows_order_id
    ON raw_article_rows(order_id);

CREATE INDEX IF NOT EXISTS idx_raw_shipment_rows_resolved_order_id
    ON raw_shipment_rows(resolved_order_id);

CREATE INDEX IF NOT EXISTS idx_shipments_direction_country
    ON shipments(direction, country);

CREATE INDEX IF NOT EXISTS idx_shipment_events_type_datetime
    ON shipment_events(event_type, event_datetime);

CREATE INDEX IF NOT EXISTS idx_article_lines_filters
    ON article_lines(direction, date_basis, event_datetime, product_id, order_id);

CREATE INDEX IF NOT EXISTS idx_article_lines_order_id
    ON article_lines(order_id);

CREATE INDEX IF NOT EXISTS idx_import_issues_file_severity
    ON import_issues(import_file_id, severity);
