from pathlib import Path

from xenosite.cites.plots import FigureWriter


class _FakeFig:
    def __init__(self) -> None:
        self.saved: list[Path] = []

    def savefig(self, path: Path | str, dpi: int = 150) -> None:  # noqa: ARG002
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"png-bytes")
        self.saved.append(p)


def test_figure_writer_always_rewrites(tmp_path: Path) -> None:
    writer = FigureWriter(tmp_path)
    fig1 = _FakeFig()
    assert writer.save("a.png", {"n": 1}, fig1) is True
    assert (tmp_path / "a.png").read_bytes() == b"png-bytes"

    fig2 = _FakeFig()
    assert writer.save("a.png", {"n": 1}, fig2) is True
    assert writer.n_written == 2
    assert len(fig2.saved) == 1


def test_plot_competitor_families(tmp_path: Path) -> None:
    from xenosite.cites.plots import plot_competitor_families

    writer = FigureWriter(tmp_path)
    competitors = {
        "metric": "unique_citing_papers_across_seed_set",
        "families": [
            {
                "family": "SMARTCyp",
                "unique_citers": 485,
                "category": "som",
            },
            {
                "family": "XenoSite (full suite)",
                "unique_citers": 777,
                "category": "suite",
            },
            {
                "family": "BioTransformer",
                "unique_citers": 509,
                "category": "metabolite",
            },
        ],
    }
    assert plot_competitor_families(competitors, writer) is True
    assert (tmp_path / "competitor_families.png").is_file()
