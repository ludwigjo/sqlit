"""DuckDB adapter for embedded analytics database."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import ColumnInfo, DatabaseAdapter, resolve_file_path

if TYPE_CHECKING:
    from ...config import ConnectionConfig


class DuckDBAdapter(DatabaseAdapter):
    """Adapter for DuckDB embedded database."""

    @property
    def name(self) -> str:
        return "DuckDB"

    @property
    def supports_multiple_databases(self) -> bool:
        return False

    @property
    def supports_stored_procedures(self) -> bool:
        return False

    def connect(self, config: "ConnectionConfig") -> Any:
        """Connect to DuckDB database file."""
        import duckdb

        file_path = resolve_file_path(config.file_path)
        return duckdb.connect(str(file_path))

    def get_databases(self, conn: Any) -> list[str]:
        """DuckDB doesn't support multiple databases - return empty list."""
        return []

    def get_tables(self, conn: Any, database: str | None = None) -> list[str]:
        """Get list of tables from DuckDB."""
        result = conn.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'main' AND table_type = 'BASE TABLE' "
            "ORDER BY table_name"
        )
        return [row[0] for row in result.fetchall()]

    def get_views(self, conn: Any, database: str | None = None) -> list[str]:
        """Get list of views from DuckDB."""
        result = conn.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'main' AND table_type = 'VIEW' "
            "ORDER BY table_name"
        )
        return [row[0] for row in result.fetchall()]

    def get_columns(
        self, conn: Any, table: str, database: str | None = None
    ) -> list[ColumnInfo]:
        """Get columns for a table from DuckDB."""
        result = conn.execute(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_schema = 'main' AND table_name = ? "
            "ORDER BY ordinal_position",
            (table,),
        )
        return [ColumnInfo(name=row[0], data_type=row[1]) for row in result.fetchall()]

    def get_procedures(self, conn: Any, database: str | None = None) -> list[str]:
        """DuckDB doesn't support stored procedures - return empty list."""
        return []

    def quote_identifier(self, name: str) -> str:
        """Quote identifier using double quotes for DuckDB."""
        return f'"{name}"'

    def build_select_query(
        self, table: str, limit: int, database: str | None = None
    ) -> str:
        """Build SELECT LIMIT query for DuckDB."""
        return f'SELECT * FROM "{table}" LIMIT {limit}'

    def execute_query(self, conn: Any, query: str) -> tuple[list[str], list[tuple]]:
        """Execute a query on DuckDB."""
        result = conn.execute(query)
        if result.description:
            columns = [col[0] for col in result.description]
            rows = result.fetchall()
            return columns, [tuple(row) for row in rows]
        return [], []

    def execute_non_query(self, conn: Any, query: str) -> int:
        """Execute a non-query on DuckDB."""
        result = conn.execute(query)
        # DuckDB doesn't provide rowcount for all operations
        try:
            return result.rowcount if hasattr(result, 'rowcount') else -1
        except Exception:
            return -1
