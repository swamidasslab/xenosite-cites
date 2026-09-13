"""Minimal importable package used as the swamidasslab Python project template."""

from template_py_project._version import __version__

__all__ = ["__version__", "hello"]


def hello(name: str = "world") -> str:
    """Return a greeting.

    >>> hello()
    'hello, world'
    >>> hello("lab")
    'hello, lab'
    """
    return f"hello, {name}"
