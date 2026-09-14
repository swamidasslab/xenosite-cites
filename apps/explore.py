# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "pandas",
#     "altair",
# ]
# ///

"""Interactive explorer for XenoSite citation analysis (static WASM / GitHub Pages)."""

import marimo

__generated_with = "0.24.2"
app = marimo.App(width="full")


@app.cell
def _():
    import json
    from pathlib import Path
    from urllib.request import urlopen

    import altair as alt
    import marimo as mo
    import pandas as pd

    return Path, alt, json, mo, pd, urlopen


@app.cell
def _(Path, json, mo, urlopen):
    def load_explorer() -> dict:
        path = mo.notebook_location() / "public" / "explorer.json"
        text = str(path)
        if text.startswith("http://") or text.startswith("https://"):
            with urlopen(text) as handle:  # noqa: S310
                return json.load(handle)
        return json.loads(Path(text).read_text(encoding="utf-8"))

    data = load_explorer()
    return (data,)


@app.cell
def _(data, mo):
    mo.md(
        f"""
# XenoSite citation explorer

Interactive view of OpenAlex citing papers for the XenoSite-family seed set.
Filters update charts and tables from the analysis payload served with this page.

- Citing papers: **{data["analysis"].get("n_citing", "—")}**
- Topics: **{len(data["analysis"].get("topics") or [])}**
- Predict-then-test high+medium: **{data["analysis"].get("n_predict_then_test_high_medium", "—")}**
"""
    )
    return


@app.cell
def _(data, pd):
    papers = pd.DataFrame(data["papers"])
    citing = papers.loc[~papers["is_seed"]].copy()
    seeds = papers.loc[papers["is_seed"]].copy()
    seed_ids = sorted(seeds["seed_id"].dropna().astype(str).unique().tolist())
    topics = data["analysis"].get("topics") or []
    topic_labels = {
        int(t["topic_id"]): f"T{t['topic_id']}: {', '.join((t.get('keywords') or [])[:4])}"
        for t in topics
        if t.get("topic_id") is not None
    }
    class_labels = sorted({c for c in citing["class_label"].dropna().astype(str).unique().tolist()})
    years = citing["year"].dropna().astype(int)
    year_min = int(years.min()) if len(years) else 2010
    year_max = int(years.max()) if len(years) else 2026
    ptt = pd.DataFrame(data.get("predict_then_test") or [])
    competitors = pd.DataFrame((data.get("competitors") or {}).get("families") or [])
    return (
        citing,
        class_labels,
        competitors,
        ptt,
        seed_ids,
        topic_labels,
        year_max,
        year_min,
    )


@app.cell
def _(class_labels, mo, seed_ids, topic_labels, year_max, year_min):
    year_range = mo.ui.range_slider(
        start=year_min,
        stop=year_max,
        value=(year_min, year_max),
        label="Year range",
        full_width=True,
    )
    class_filter = mo.ui.multiselect(
        options=class_labels,
        value=class_labels,
        label="Class",
    )
    topic_options = ["(any)"] + [topic_labels[k] for k in sorted(topic_labels)]
    topic_filter = mo.ui.dropdown(options=topic_options, value="(any)", label="Topic")
    seed_filter = mo.ui.dropdown(
        options=["(any)"] + seed_ids,
        value="(any)",
        label="Cites seed",
    )
    ptt_filter = mo.ui.dropdown(
        options=["(any)", "high", "medium", "low", "none"],
        value="(any)",
        label="Predict-then-test",
    )
    query = mo.ui.text(
        placeholder="Search title / venue / DOI…",
        label="Search",
        full_width=True,
    )
    mo.vstack(
        [
            year_range,
            mo.hstack([class_filter, topic_filter, seed_filter, ptt_filter], wrap=True),
            query,
        ],
        gap=0.5,
    )
    return class_filter, ptt_filter, query, seed_filter, topic_filter, year_range


@app.cell
def _(
    citing,
    class_filter,
    ptt_filter,
    query,
    seed_filter,
    topic_filter,
    topic_labels,
    year_range,
):
    filtered = citing.copy()
    y0, y1 = year_range.value
    filtered = filtered[filtered["year"].fillna(0).astype(int).between(y0, y1)]
    if class_filter.value:
        filtered = filtered[filtered["class_label"].isin(class_filter.value)]
    if topic_filter.value != "(any)":
        wanted = {tid for tid, label in topic_labels.items() if label == topic_filter.value}
        filtered = filtered[filtered["topic_id"].isin(wanted)]
    if seed_filter.value != "(any)":
        sid = seed_filter.value
        filtered = filtered[
            filtered["cites_seed_ids"].map(lambda val: isinstance(val, list) and sid in val)
        ]
    if ptt_filter.value != "(any)":
        conf = filtered["predict_then_test_confidence"].fillna("none").astype(str)
        filtered = filtered[conf == ptt_filter.value]
    q = (query.value or "").strip().lower()
    if q:
        blob = (
            filtered["title"].fillna("").astype(str)
            + " "
            + filtered["venue"].fillna("").astype(str)
            + " "
            + filtered["doi"].fillna("").astype(str)
        ).str.lower()
        filtered = filtered[blob.str.contains(q, regex=False)]
    return (filtered,)


@app.cell
def _(alt, filtered, mo):
    n = len(filtered)
    by_year = (
        filtered.dropna(subset=["year"])
        .assign(year=lambda d: d["year"].astype(int))
        .groupby("year", as_index=False)
        .size()
        .rename(columns={"size": "papers"})
    )
    by_class = (
        filtered.fillna({"class_label": "unknown"})
        .groupby("class_label", as_index=False)
        .size()
        .rename(columns={"size": "papers"})
    )
    year_chart = (
        alt.Chart(by_year)
        .mark_bar()
        .encode(
            x=alt.X("year:O", title="Year"),
            y=alt.Y("papers:Q", title="Citing papers"),
            tooltip=["year", "papers"],
        )
        .properties(height=220, title=f"Filtered citing papers by year (n={n})")
    )
    class_chart = (
        alt.Chart(by_class)
        .mark_bar()
        .encode(
            x=alt.X("papers:Q", title="Papers"),
            y=alt.Y("class_label:N", sort="-x", title="Class"),
            tooltip=["class_label", "papers"],
        )
        .properties(height=220, title="Class mix (filtered)")
    )
    mo.hstack([year_chart, class_chart], widths="equal", gap=1)
    return


@app.cell
def _(alt, filtered, mo):
    exploded = filtered.explode("cites_seed_ids").dropna(subset=["cites_seed_ids"])
    if len(exploded) == 0:
        mo.md("_No seed edges in the current filter._")
    else:
        by_seed = (
            exploded.groupby("cites_seed_ids", as_index=False)
            .size()
            .rename(columns={"cites_seed_ids": "seed_id", "size": "papers"})
            .sort_values("papers", ascending=False)
        )
        (
            alt.Chart(by_seed)
            .mark_bar()
            .encode(
                x=alt.X("papers:Q", title="Citing papers (filtered)"),
                y=alt.Y("seed_id:N", sort="-x", title="Seed"),
                tooltip=["seed_id", "papers"],
            )
            .properties(
                height=max(220, 18 * len(by_seed)),
                title="Citations per seed (filtered)",
            )
        )
    return


@app.cell
def _(filtered, mo):
    show = filtered[
        [
            "year",
            "title",
            "class_label",
            "topic_id",
            "predict_then_test_confidence",
            "venue",
            "doi",
            "cites_seed_ids",
            "cited_by_count",
        ]
    ].copy()
    show = show.sort_values(
        by=["year", "cited_by_count"],
        ascending=[False, False],
        na_position="last",
    )
    mo.ui.table(
        show.head(250),
        selection=None,
        label=f"Matching papers (showing {min(250, len(show))} of {len(show)})",
        page_size=25,
    )
    return


@app.cell
def _(mo, ptt):
    mo.md(
        """
## Predict-then-test candidates

Papers inferred to use a XenoSite-family tool and then test experimentally.
"""
    )
    ptt_conf = mo.ui.multiselect(
        options=(
            sorted(ptt["confidence"].dropna().astype(str).unique().tolist())
            if not ptt.empty
            else ["high", "medium", "low"]
        ),
        value=["high", "medium"],
        label="PTT confidence",
    )
    ptt_conf
    return (ptt_conf,)


@app.cell
def _(mo, ptt, ptt_conf):
    if ptt.empty:
        mo.md("_No candidates in payload._")
    else:
        view = ptt[ptt["confidence"].isin(ptt_conf.value)].copy()
        view = view.sort_values(
            ["confidence", "score", "year"],
            ascending=[True, False, False],
        )
        cols = [
            c
            for c in [
                "year",
                "title",
                "confidence",
                "score",
                "venue",
                "doi",
                "cites_seed_ids",
                "reasons",
                "abstract",
            ]
            if c in view.columns
        ]
        mo.ui.table(
            view[cols].head(100),
            selection=None,
            label=f"PTT rows (showing {min(100, len(view))} of {len(view)})",
            page_size=20,
        )
    return


@app.cell
def _(alt, competitors, mo):
    mo.md(
        """
## Competitor approaches (combined seeds)

Fair comparison uses the union of citing works across each tool family's method
papers (not a single flagship).
"""
    )
    if competitors.empty:
        mo.md("_No competitor summary in payload._")
    else:
        chart = (
            alt.Chart(competitors)
            .mark_bar()
            .encode(
                x=alt.X("unique_citers:Q", title="Unique citing papers"),
                y=alt.Y("family:N", sort="-x", title="Approach"),
                tooltip=["family", "n_seeds", "unique_citers", "niche", "notes"],
            )
            .properties(
                height=280,
                title="Unique citers across each approach's seed set",
            )
        )
        mo.vstack([chart, mo.ui.table(competitors, selection=None, page_size=12)])
    return


if __name__ == "__main__":
    app.run()
