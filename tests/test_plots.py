from pathlib import Path

from xenosite.cites.plots import FigureWriter, figure_data_fingerprint


class _FakeFig:
    def __init__(self) -> None:
        self.saved: list[Path] = []

    def savefig(self, path: Path | str, dpi: int = 150) -> None:  # noqa: ARG002
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"png-bytes")
        self.saved.append(p)


def test_fingerprint_stable() -> None:
    a = figure_data_fingerprint({"years": [2020, 2021], "counts": [1, 2]})
    b = figure_data_fingerprint({"counts": [1, 2], "years": [2020, 2021]})
    c = figure_data_fingerprint({"years": [2020, 2021], "counts": [1, 3]})
    assert a == b
    assert a != c


def test_figure_writer_skips_unchanged_data(tmp_path: Path) -> None:
    writer = FigureWriter(tmp_path)
    fig1 = _FakeFig()
    assert writer.save("a.png", {"n": 1}, fig1) is True
    assert (tmp_path / "a.png").read_bytes() == b"png-bytes"
    writer.flush()

    writer2 = FigureWriter(tmp_path)
    fig2 = _FakeFig()
    assert writer2.save("a.png", {"n": 1}, fig2) is False
    assert fig2.saved == []
    assert writer2.n_written == 0

    fig3 = _FakeFig()
    assert writer2.save("a.png", {"n": 2}, fig3) is True
    assert writer2.n_written == 1


def test_figure_writer_bootstraps_existing_png_without_rewrite(tmp_path: Path) -> None:
    png = tmp_path / "a.png"
    png.write_bytes(b"existing")
    writer = FigureWriter(tmp_path)
    fig = _FakeFig()
    assert writer.save("a.png", {"n": 1}, fig) is False
    assert png.read_bytes() == b"existing"
    assert fig.saved == []
    assert writer.flush() is True
    # Second run: still no rewrite
    writer2 = FigureWriter(tmp_path)
    fig2 = _FakeFig()
    assert writer2.save("a.png", {"n": 1}, fig2) is False
    assert png.read_bytes() == b"existing"
