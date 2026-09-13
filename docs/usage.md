# Usage

```bash
uv sync --group dev
```

```python
from xenosite.cites import load_seeds

seeds = load_seeds()
assert seeds[0].normalized_doi().startswith("10.")
```

Edit `src/xenosite/cites/seeds.yaml` to add or retire seed papers. Keep bulk downloads and API caches under `artifacts/` (not committed).
