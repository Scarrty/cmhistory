import re
from pathlib import Path

WIKI_DIR = Path("docs/wiki")
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def test_required_wiki_pages_exist() -> None:
    required_pages = {
        "Home.md",
        "Cardmarket-Exporte.md",
        "Installation.md",
        "Erster-Datenbankaufbau.md",
        "Monatlicher-Import.md",
        "Dashboard-und-Reports.md",
        "Betrieb-und-Konfiguration.md",
        "Datenschutz-und-Backups.md",
        "Fehlerbehebung.md",
        "Release-v1.0.0.md",
        "_Sidebar.md",
        "_Footer.md",
    }

    assert required_pages.issubset(path.name for path in WIKI_DIR.glob("*.md"))


def test_internal_wiki_links_resolve() -> None:
    missing_links: list[str] = []
    for page in WIKI_DIR.glob("*.md"):
        content = page.read_text(encoding="utf-8")
        for target in MARKDOWN_LINK.findall(content):
            if target.startswith(("http://", "https://", "#")):
                continue
            target_path = target.split("#", maxsplit=1)[0]
            if not target_path.endswith(".md"):
                target_path += ".md"
            if not (WIKI_DIR / target_path).is_file():
                missing_links.append(f"{page.name}: {target}")

    assert missing_links == []


def test_wiki_documents_release_version() -> None:
    home = (WIKI_DIR / "Home.md").read_text(encoding="utf-8")
    release = (WIKI_DIR / "Release-v1.0.0.md").read_text(encoding="utf-8")
    footer = (WIKI_DIR / "_Footer.md").read_text(encoding="utf-8")

    assert "1.0.0" in home
    assert "Normalisierungsversion 3" in release
    assert "100 % AI-generated / Best Effort" in home
    assert "100 % AI-generated / Best Effort" in footer
