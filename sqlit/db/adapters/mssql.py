"""Microsoft SQL Server adapter using pyodbc."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import ColumnInfo, DatabaseAdapter

if TYPE_CHECKING:
    from ...config import ConnectionConfig


class SQLServerAdapter(DatabaseAdapter):
    """Adapter for Microsoft SQL Server using pyodbc."""

    @property
    def name(self) -> str:
        return "SQL Server"

    @property
    def supports_multiple_databases(self) -> bool:
        return True

    @property
    def supports_stored_procedures(self) -> bool:
        return True

    def connect(self, config: "ConnectionConfig") -> Any:
        """Connect to SQL Server using pyodbc."""
        import pyodbc

        conn_str = config.get_connection_string()
        return pyodbc.connect(conn_str, timeout=10)

    def get_databases(self, conn: Any) -> list[str]:
        """Get list of databases from SQL Server."""
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sys.databases ORDER BY name")
        return [row[0] for row in cursor.fetchall()]

    def get_tables(self, conn: Any, database: str | None = None) -> list[str]:
        """Get list of tables from SQL Server."""
        cursor = conn.cursor()
        if database:
            cursor.execute(
                f"SELECT TABLE_NAME FROM [{database}].INFORMATION_SCHEMA.TABLES "
                f"WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME"
            )
        else:
            cursor.execute(
                "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
                "WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME"
            )
        return [row[0] for row in cursor.fetchall()]

    def get_views(self, conn: Any, database: str | None = None) -> list[str]:
        """Get list of views from SQL Server."""
        cursor = conn.cursor()
        if database:
            cursor.execute(
                f"SELECT TABLE_NAME FROM [{database}].INFORMATION_SCHEMA.VIEWS "
                f"ORDER BY TABLE_NAME"
            )
        else:
            cursor.execute(
                "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.VIEWS ORDER BY TABLE_NAME"
            )
        return [row[0] for row in cursor.fetchall()]

    def get_columns(
        self, conn: Any, table: str, database: str | None = None
    ) -> list[ColumnInfo]:
        """Get columns for a table from SQL Server."""
        cursor = conn.cursor()
        if database:
            cursor.execute(
                f"SELECT COLUMN_NAME, DATA_TYPE FROM [{database}].INFORMATION_SCHEMA.COLUMNS "
                f"WHERE TABLE_NAME = ? ORDER BY ORDINAL_POSITION",
                (table,),
            )
        else:
            cursor.execute(
                "SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS "
                "WHERE TABLE_NAME = ? ORDER BY ORDINAL_POSITION",
                (table,),
            )
        return [ColumnInfo(name=row[0], data_type=row[1]) for row in cursor.fetchall()]

    def get_procedures(self, conn: Any, database: str | None = None) -> list[str]:
        """Get stored procedures from SQL Server."""
        cursor = conn.cursor()
        if database:
            cursor.execute(
                f"SELECT ROUTINE_NAME FROM [{database}].INFORMATION_SCHEMA.ROUTINES "
                f"WHERE ROUTINE_TYPE = 'PROCEDURE' ORDER BY ROUTINE_NAME"
            )
        else:
            cursor.execute(
                "SELECT ROUTINE_NAME FROM INFORMATION_SCHEMA.ROUTINES "
                "WHERE ROUTINE_TYPE = 'PROCEDURE' ORDER BY ROUTINE_NAME"
            )
        return [row[0] for row in cursor.fetchall()]

    def quote_identifier(self, name: str) -> str:
        """Quote identifier using SQL Server brackets."""
        return f"[{name}]"

    def build_select_query(
        self, table: str, limit: int, database: str | None = None
    ) -> str:
        """Build SELECT TOP query for SQL Server."""
        if database:
            return f"SELECT TOP {limit} * FROM [{database}].[dbo].[{table}]"
        return f"SELECT TOP {limit} * FROM [{table}]"

    def execute_query(self, conn: Any, query: str) -> tuple[list[str], list[tuple]]:
        """Execute a query on SQL Server."""
        cursor = conn.cursor()
        cursor.execute(query)
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            return columns, [tuple(row) for row in rows]
        return [], []

    def execute_non_query(self, conn: Any, query: str) -> int:
        """Execute a non-query on SQL Server."""
        cursor = conn.cursor()
        cursor.execute(query)
        rowcount = cursor.rowcount
        conn.commit()
        return rowcount
