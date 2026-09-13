"""Study citations to XenoSite papers."""

try:
    from ._version import __version__
except ImportError:  # pragma: no cover - missing only in incomplete checkouts
    __version__ = "0.0.0"

from .seeds import SeedPaper, load_seeds

__all__ = ["__version__", "SeedPaper", "load_seeds"]
