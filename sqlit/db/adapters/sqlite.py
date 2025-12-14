"""SQLite adapter using built-in sqlite3."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING, Any

from .base import ColumnInfo, DatabaseAdapter, resolve_file_path

if TYPE_CHECKING:
    from ...config import ConnectionConfig


class SQLiteAdapter(DatabaseAdapter):
    """Adapter for SQLite using built-in sqlite3."""

    @property
    def name(self) -> str:
        return "SQLite"

    @property
    def supports_multiple_databases(self) -> bool:
        return False

    @property
    def supports_stored_procedures(self) -> bool:
        return False

    def connect(self, config: "ConnectionConfig") -> Any:
        """Connect to SQLite database file."""
        file_path = resolve_file_path(config.file_path)
        conn = sqlite3.connect(file_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_databases(self, conn: Any) -> list[str]:
        """SQLite doesn't support multiple databases - return empty list."""
        return []

    def get_tables(self, conn: Any, database: str | None = None) -> list[str]:
        """Get list of tables from SQLite."""
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        return [row[0] for row in cursor.fetchall()]

    def get_views(self, conn: Any, database: str | None = None) -> list[str]:
        """Get list of views from SQLite."""
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='view' ORDER BY name"
        )
        return [row[0] for row in cursor.fetchall()]

    def get_columns(
        self, conn: Any, table: str, database: str | None = None
    ) -> list[ColumnInfo]:
        """Get columns for a table from SQLite."""
        cursor = conn.cursor()
        cursor.execute(f'PRAGMA table_info("{table}")')
        # PRAGMA table_info returns: cid, name, type, notnull, dflt_value, pk
        return [ColumnInfo(name=row[1], data_type=row[2] or "TEXT") for row in cursor.fetchall()]

    def get_procedures(self, conn: Any, database: str | None = None) -> list[str]:
        """SQLite doesn't support stored procedures - return empty list."""
        return []

    def quote_identifier(self, name: str) -> str:
        """Quote identifier using double quotes for SQLite."""
        return f'"{name}"'

    def build_select_query(
        self, table: str, limit: int, database: str | None = None
    ) -> str:
        """Build SELECT LIMIT query for SQLite."""
        return f'SELECT * FROM "{table}" LIMIT {limit}'

    def execute_query(self, conn: Any, query: str) -> tuple[list[str], list[tuple]]:
        """Execute a query on SQLite."""
        cursor = conn.cursor()
        cursor.execute(query)
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            return columns, [tuple(row) for row in rows]
        return [], []

    def execute_non_query(self, conn: Any, query: str) -> int:
        """Execute a non-query on SQLite."""
        cursor = conn.cursor()
        cursor.execute(query)
        rowcount = cursor.rowcount
        conn.commit()
        return rowcount
