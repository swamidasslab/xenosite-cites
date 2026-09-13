from pathlib import Path

import pytest

from xenosite.cites import SeedPaper, load_seeds
from xenosite.cites.seeds import load_seeds as load_seeds_uncached


@pytest.fixture(autouse=True)
def _clear_seed_cache() -> None:
    load_seeds_uncached.cache_clear()


def test_load_packaged_seeds() -> None:
    seeds = load_seeds()
    assert len(seeds) >= 15
    ids = {s.id for s in seeds}
    assert "zaretzki-2013-xenosite" in ids
    assert "flynn-2020-xenonet" in ids
    assert "dang-2017-casa" in ids
    assert "hughes-2020-metabolic-forest" in ids
    assert all(s.normalized_doi().startswith("10.") for s in seeds)
    assert any("xenosite" in s.tags for s in seeds)


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
        load_seeds(str(path))


def test_load_seeds_rejects_duplicate_dois(tmp_path: Path) -> None:
    path = tmp_path / "seeds.yaml"
    path.write_text(
        """
papers:
  - id: a
    doi: 10.1/same
    title: A
    year: 2000
  - id: b
    doi: https://doi.org/10.1/same
    title: B
    year: 2001
""",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate seed DOI"):
        load_seeds(str(path))
