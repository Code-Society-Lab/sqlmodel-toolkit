"""A toolkit for cleaner SQLModel queries with fluent API, Model base class, and engine management"""

from .model import Model
from .query import Query

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("sqlmodel_toolkit")
except PackageNotFoundError:
    from sqlmodel_toolkit._version import version as __version__

__all__ = ["Model", "Query", "__version__"]
