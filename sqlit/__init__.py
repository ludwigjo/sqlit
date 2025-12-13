"""sqlit - A terminal UI for SQL Server."""

__version__ = "0.1.0"
__author__ = "Peter"

from .cli import main
from .app import SSMSTUI
from .config import AuthType, ConnectionConfig

__all__ = [
    "main",
    "SSMSTUI",
    "AuthType",
    "ConnectionConfig",
]
