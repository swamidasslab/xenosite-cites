"""Basic topic analysis over citing-paper abstracts/titles."""

from __future__ import annotations

from typing import Any

from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer


def _doc_text(paper: dict[str, Any]) -> str:
    title = str(paper.get("title") or "").strip()
    abstract = str(paper.get("abstract") or "").strip()
    if abstract:
        return f"{title}. {abstract}"
    return title


def fit_topics(
    papers: list[dict[str, Any]],
    *,
    n_topics: int = 8,
    max_features: int = 4000,
    random_state: int = 0,
) -> dict[str, Any]:
    """TF-IDF + NMF topics for papers with usable text.

    Returns topic keywords, per-paper topic id/weight, and model diagnostics.
    """
    docs: list[str] = []
    index: list[int] = []
    for i, paper in enumerate(papers):
        text = _doc_text(paper)
        if len(text.split()) >= 8:
            docs.append(text)
            index.append(i)

    if len(docs) < n_topics:
        n_topics = max(2, len(docs) // 3) if len(docs) >= 2 else 0
    if n_topics < 2:
        return {
            "n_topics": 0,
            "n_docs": len(docs),
            "topics": [],
            "assignments": [],
        }

    vectorizer = TfidfVectorizer(
        max_features=max_features,
        stop_words="english",
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.85,
    )
    matrix = vectorizer.fit_transform(docs)
    model = NMF(
        n_components=n_topics,
        init="nndsvda",
        random_state=random_state,
        max_iter=400,
    )
    weights = model.fit_transform(matrix)
    terms = vectorizer.get_feature_names_out()

    topics: list[dict[str, Any]] = []
    for t in range(n_topics):
        top_idx = model.components_[t].argsort()[::-1][:12]
        topics.append(
            {
                "topic_id": t,
                "keywords": [str(terms[j]) for j in top_idx],
                "n_papers": int((weights.argmax(axis=1) == t).sum()),
            }
        )

    assignments: list[dict[str, Any]] = []
    for row, paper_i in enumerate(index):
        topic_id = int(weights[row].argmax())
        assignments.append(
            {
                "paper_index": paper_i,
                "openalex_id": papers[paper_i].get("openalex_id"),
                "topic_id": topic_id,
                "topic_weight": float(weights[row, topic_id]),
            }
        )

    # Refresh topic sizes from assignments (same as above, keep consistent).
    sizes = [0] * n_topics
    for a in assignments:
        sizes[a["topic_id"]] += 1
    for t, topic in enumerate(topics):
        topic["n_papers"] = sizes[t]

    return {
        "n_topics": n_topics,
        "n_docs": len(docs),
        "topics": topics,
        "assignments": assignments,
        "reconstruction_error": float(model.reconstruction_err_),
    }
