from hypothesis import given
from hypothesis import strategies as st

from template_py_project import hello


def test_hello_default() -> None:
    assert hello() == "hello, world"


@given(st.text(min_size=0, max_size=40))
def test_hello_includes_name(name: str) -> None:
    assert hello(name).startswith("hello, ")
    assert hello(name) == f"hello, {name}"
