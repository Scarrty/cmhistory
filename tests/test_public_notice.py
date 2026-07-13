from pathlib import Path


def test_ai_generated_best_effort_notice_is_present_on_public_surfaces() -> None:
    public_surfaces = (
        Path("README.md"),
        Path("NOTICE.md"),
        Path("docs/releases/v1.0.0.md"),
        Path("docs/wiki/Home.md"),
        Path("docs/wiki/_Footer.md"),
        Path("src/cm_dashboard/web/templates/base.html"),
    )

    for path in public_surfaces:
        content = path.read_text(encoding="utf-8")
        assert "AI-generated" in content, f"Missing AI-generated notice in {path}"
        assert "Best Effort" in content or "Best-Effort" in content, (
            f"Missing best-effort notice in {path}"
        )


def test_readme_contains_release_and_technology_badges() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    for badge in ("Release", "CI", "Python", "FastAPI", "SQLite", "Jinja", "pytest", "Ruff"):
        assert f"![{badge}]" in readme or f"[![{badge}]" in readme
