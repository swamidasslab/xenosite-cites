from pathlib import Path

import pytest

from xenosite.cites import SeedPaper, load_seeds


def test_load_packaged_seeds() -> None:
    seeds = load_seeds()
    assert len(seeds) >= 3
    ids = {s.id for s in seeds}
    assert "zaretzki-2013-xenosite" in ids
    assert all(s.normalized_doi().startswith("10.") for s in seeds)


def test_normalized_doi_strips_prefix() -> None:
    paper = SeedPaper(
        id="x",
        doi="https://doi.org/10.1021/ci400518g",
        title="t",
        year=2013,
    )
    assert paper.normalized_doi() == "10.1021/ci400518g"


def test_load_seeds_rejects_duplicate_ids(tmp_path: Path) -> None:
    path = tmp_path / "seeds.yaml"
    path.write_text(
        """
papers:
  - id: a
    doi: 10.1/a
    title: A
    year: 2000
  - id: a
    doi: 10.1/b
    title: B
    year: 2001
""",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate seed id"):
        load_seeds(path)
