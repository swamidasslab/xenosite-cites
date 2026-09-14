"""Figures for citing-paper bibliometrics and labels."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402


class FigureWriter:
    """Always write PNGs under ``fig_dir`` (rebuild on every analyze/Pages run)."""

    def __init__(self, fig_dir: Path) -> None:
        self.fig_dir = fig_dir
        self.n_written = 0

    def save(self, name: str, data: Any, fig: Any, *, dpi: int = 150) -> bool:  # noqa: ARG002
        path = self.fig_dir / name
        self.fig_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=dpi)
        self._close(fig)
        self.n_written += 1
        return True

    def flush(self) -> bool:
        return False

    @staticmethod
    def _close(fig: Any) -> None:
        if isinstance(fig, Figure):
            plt.close(fig)


def _citing(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [p for p in papers if not p.get("is_seed")]


def plot_citations_by_year(
    papers: list[dict[str, Any]],
    writer: FigureWriter,
    *,
    min_year: int = 2012,
) -> bool:
    years: list[int] = []
    for paper in _citing(papers):
        year = paper.get("year")
        if isinstance(year, int) and year >= min_year:
            years.append(year)
    counts = Counter(years)
    xs = sorted(counts)
    ys = [counts[x] for x in xs]
    data = {"counts": ys, "min_year": min_year, "years": xs}
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(xs, ys, color="#2c6e8a", width=0.8)
    ax.set_xlabel("Year")
    ax.set_ylabel("Citing papers")
    ax.set_title("XenoSite-family citations by year")
    ax.set_xticks(xs[:: max(1, len(xs) // 10)] if xs else [])
    fig.tight_layout()
    return writer.save("citations_by_year.png", data, fig)


def plot_top_venues(
    papers: list[dict[str, Any]], writer: FigureWriter, *, top_n: int = 15
) -> bool:
    venues = Counter(p.get("venue") for p in _citing(papers) if p.get("venue"))
    top = venues.most_common(top_n)
    labels = [v for v, _ in top][::-1]
    vals = [c for _, c in top][::-1]
    data = {"top_n": top_n, "venues": labels, "counts": vals}
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(labels, vals, color="#3d7a5c")
    ax.set_xlabel("Citing papers")
    ax.set_title(f"Top {top_n} venues")
    fig.tight_layout()
    return writer.save("top_venues.png", data, fig)


def plot_citations_per_seed(summary: dict[str, Any], writer: FigureWriter) -> bool:
    per = summary.get("citations_per_seed") or {}
    items = sorted(per.items(), key=lambda kv: kv[1])
    labels = [k for k, _ in items]
    vals = [v for _, v in items]
    data = {"seeds": labels, "counts": vals}
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.barh(labels, vals, color="#8a4b2c")
    ax.set_xlabel("Citing works (OpenAlex)")
    ax.set_title("Citations per seed paper")
    fig.tight_layout()
    return writer.save("citations_per_seed.png", data, fig)


def plot_class_counts(labels: list[str], writer: FigureWriter) -> bool:
    order = ["experimental", "computational", "review", "unknown"]
    counts = Counter(labels)
    xs = [k for k in order if counts.get(k)]
    ys = [counts[k] for k in xs]
    data = {"classes": xs, "counts": ys}
    colors = {
        "computational": "#2c6e8a",
        "experimental": "#8a4b2c",
        "review": "#3d7a5c",
        "unknown": "#888888",
    }
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(xs, ys, color=[colors.get(x, "#444") for x in xs])
    ax.set_ylabel("Citing papers")
    ax.set_title("Paper class (wet-lab if any; else computation-only)")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    return writer.save("class_counts.png", data, fig)


def plot_class_by_year(
    papers: list[dict[str, Any]],
    label_by_id: dict[str, str],
    writer: FigureWriter,
    *,
    min_year: int = 2012,
) -> bool:
    classes = ["experimental", "computational", "review", "unknown"]
    year_class: dict[int, Counter[str]] = {}
    for paper in _citing(papers):
        year = paper.get("year")
        if not isinstance(year, int) or year < min_year:
            continue
        oid = str(paper.get("openalex_id") or "")
        label = label_by_id.get(oid, "unknown")
        year_class.setdefault(year, Counter())[label] += 1
    years = sorted(year_class)
    series = {cls: [year_class[y].get(cls, 0) for y in years] for cls in classes}
    data = {"years": years, "series": series, "min_year": min_year}
    fig, ax = plt.subplots(figsize=(9, 4.5))
    bottoms = [0] * len(years)
    palette = {
        "experimental": "#8a4b2c",
        "computational": "#2c6e8a",
        "review": "#3d7a5c",
        "unknown": "#bbbbbb",
    }
    for cls in classes:
        vals = series[cls]
        if not any(vals):
            continue
        ax.bar(years, vals, bottom=bottoms, label=cls, color=palette[cls], width=0.85)
        bottoms = [b + v for b, v in zip(bottoms, vals, strict=True)]
    ax.set_xlabel("Year")
    ax.set_ylabel("Citing papers")
    ax.set_title("Class mix by year")
    ax.legend(frameon=False, ncol=3, fontsize=8)
    fig.tight_layout()
    return writer.save("class_by_year.png", data, fig)


def plot_topic_sizes(topics: list[dict[str, Any]], writer: FigureWriter) -> bool:
    if not topics:
        data: dict[str, Any] = {"topics": []}
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.text(0.5, 0.5, "No topics fit", ha="center", va="center")
        ax.axis("off")
        return writer.save("topic_sizes.png", data, fig)
    rows = []
    labels = []
    vals = []
    for t in sorted(topics, key=lambda x: x["n_papers"]):
        kw = ", ".join(t["keywords"][:4])
        labels.append(f"T{t['topic_id']}: {kw}")
        vals.append(t["n_papers"])
        rows.append(
            {
                "topic_id": t["topic_id"],
                "n_papers": t["n_papers"],
                "keywords": t["keywords"][:4],
            }
        )
    data = {"topics": rows}
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(labels, vals, color="#2c6e8a")
    ax.set_xlabel("Papers (primary topic)")
    ax.set_title("NMF topics from citing abstracts/titles")
    fig.tight_layout()
    return writer.save("topic_sizes.png", data, fig)


def plot_predict_then_test_counts(confidences: list[str], writer: FigureWriter) -> bool:
    order = ["high", "medium", "low"]
    counts = Counter(confidences)
    xs = [k for k in order if counts.get(k)]
    ys = [counts[k] for k in xs]
    data = {"levels": xs, "counts": ys}
    colors = {"high": "#2c6e8a", "medium": "#8a4b2c", "low": "#bbbbbb"}
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(xs, ys, color=[colors.get(x, "#444") for x in xs])
    ax.set_ylabel("Papers")
    ax.set_title("Predict-then-test candidates (XenoSite → experiment)")
    fig.tight_layout()
    return writer.save("predict_then_test_counts.png", data, fig)
