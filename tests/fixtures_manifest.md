# Source Fixture Manifest

> **AI-/Best-Effort-Hinweis:** Projekt und Testdokumentation wurden zu 100 % mit KI generiert.
> Keine Gewaehr; siehe [NOTICE.md](../NOTICE.md).

These fixtures reference real local Cardmarket export files by path. The files are not copied into
the repository because they contain private account and transaction data.

Default source root: `D:\OneDrive\Dokumente\CM History`

Set `CM_DASHBOARD_SOURCE_ROOT` to use a different local source folder.

| Key | Relative path | Purpose |
|---|---|---|
| `tolerant_xls` | `PURCHASED ARTICLES-BYPAYMENTDATE-2016-06-01_2016-06-30.XLS` | XLS parser tolerance fixture. |
| `unicode_shipment` | `PURCHASED SHIPMENTS-BYPAYMENTDATE-2016-06-01_2016-06-30.XLS` | Unicode fidelity and grouped shipment rows. |
| `sold_articles_2026_01_csv` | `SOLD ARTICLES-BYPURCHASEDATE-2026-01-01_2026-01-31.CSV` | CSV side of known duplicate CSV/XLS pair. |
| `sold_articles_2026_01_xls` | `SOLD ARTICLES-BYPURCHASEDATE-2026-01-01_2026-01-31.XLS` | XLS side of known duplicate CSV/XLS pair. |
| `purchased_missing_2024_06_payment_articles` | `PURCHASED ARTICLES-BYPAYMENTDATE-2024-06-01_2024-06-30.XLS` | Missing purchase-date coverage comparison. |
| `sold_missing_2019_01_payment_articles` | `SOLD ARTICLES-BYPAYMENTDATE-2019-01-01_2019-01-31.XLS` | Sold coverage gap comparison. |
| `sold_missing_2025_08_purchase_articles` | `SOLD ARTICLES-BYPURCHASEDATE-2025-08-01_2025-08-31.XLS` | Sold purchase-date coverage gap comparison. |
| `charizard_2016_payment_articles` | `PURCHASED ARTICLES-BYPAYMENTDATE-2016-10-01_2016-10-31.XLS` | Product detail localized label fixture with Charizard label. |
| `charizard_2020_payment_articles` | `PURCHASED ARTICLES-BYPAYMENTDATE-2020-04-01_2020-04-30.XLS` | Product detail localized label fixture with Glurak label. |
