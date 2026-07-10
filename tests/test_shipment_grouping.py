from collections import defaultdict

from cm_dashboard.importing.filename import DateBasis, ExportEntity
from cm_dashboard.importing.readers import read_spreadsheet
from cm_dashboard.importing.shipment_grouping import resolve_shipment_groups
from cm_dashboard.importing.source_scan import scan_source_files
from tests.fixtures import require_fixture_path, source_root


def test_shipment_grouping_forward_fills_continuation_rows_from_previous_header() -> None:
    sheet = read_spreadsheet(require_fixture_path("unicode_shipment"))
    rows = resolve_shipment_groups(sheet)

    header_index = next(
        index
        for index, row in enumerate(rows[:-1])
        if row.is_header_row and not rows[index + 1].is_header_row
    )
    header_row = rows[header_index]
    continuation_row = rows[header_index + 1]

    assert header_row.is_header_row
    assert header_row.order_id is not None
    assert continuation_row.is_header_row is False
    assert continuation_row.order_id is None
    assert continuation_row.resolved_order_id == header_row.order_id
    assert continuation_row.values["OrderID"] == ""
    assert continuation_row.inherited_values["OrderID"] == header_row.values["OrderID"]
    assert continuation_row.inherited_values["Username"] == header_row.values["Username"]
    assert continuation_row.inherited_values["Product ID"] == continuation_row.values["Product ID"]
    assert continuation_row.inherited_values["Localized Product Name"]


def test_shipment_grouping_preserves_source_row_numbers() -> None:
    sheet = read_spreadsheet(require_fixture_path("unicode_shipment"))
    rows = resolve_shipment_groups(sheet)

    assert [row.source_row_number for row in rows] == list(range(2, len(rows) + 2))


def test_shipment_group_counts_match_review_evidence() -> None:
    expected = {
        ("PURCHASED", DateBasis.PAYMENTDATE): (3657, 740, 2917, 740),
        ("PURCHASED", DateBasis.PURCHASEDATE): (3657, 740, 2917, 740),
        ("SOLD", DateBasis.PAYMENTDATE): (1641, 342, 1299, 342),
        ("SOLD", DateBasis.PURCHASEDATE): (1641, 342, 1299, 342),
    }

    counts: dict[tuple[str, DateBasis], dict[str, set[str] | int]] = defaultdict(
        lambda: {"rows": 0, "headers": 0, "continuations": 0, "orders": set()}
    )
    report = scan_source_files(source_root())
    for source_file in report.files:
        metadata = source_file.metadata
        if metadata.entity != ExportEntity.SHIPMENTS:
            continue

        rows = resolve_shipment_groups(read_spreadsheet(source_file.path))
        key = (metadata.direction.value, metadata.date_basis)
        counts[key]["rows"] += len(rows)
        counts[key]["headers"] += sum(row.is_header_row for row in rows)
        counts[key]["continuations"] += sum(not row.is_header_row for row in rows)
        order_set = counts[key]["orders"]
        assert isinstance(order_set, set)
        order_set.update(row.order_id for row in rows if row.order_id is not None)

    for key, (rows, headers, continuations, unique_orders) in expected.items():
        order_set = counts[key]["orders"]
        assert isinstance(order_set, set)
        assert counts[key]["rows"] == rows
        assert counts[key]["headers"] == headers
        assert counts[key]["continuations"] == continuations
        assert len(order_set) == unique_orders
