# Usage

Install in another project with uv (after it is published or via a git dependency):

```bash
uv add template-py-project
```

From a checkout:

```bash
uv sync --group dev
```

```python
from template_py_project import hello

assert hello("lab") == "hello, lab"
```

Public API is `hello` and `__version__`. Replace this module when you start a real package from the template.
