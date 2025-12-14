"""Query execution mixin for SSMSTUI."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from textual.widgets import DataTable, TextArea

if TYPE_CHECKING:
    from ...config import ConnectionConfig
    from ...widgets import VimMode


class QueryMixin:
    """Mixin providing query execution functionality."""

    # These attributes are defined in the main app class
    current_connection: Any
    current_config: "ConnectionConfig | None"
    current_adapter: Any
    vim_mode: "VimMode"
    _last_result_columns: list[str]
    _last_result_rows: list[tuple]
    _last_result_row_count: int

    def action_execute_query(self) -> None:
        """Execute the current query."""
        self._execute_query_common(keep_insert_mode=False)

    def action_execute_query_insert(self) -> None:
        """Execute query in INSERT mode without leaving it."""
        self._execute_query_common(keep_insert_mode=True)

    def _execute_query_common(self, keep_insert_mode: bool) -> None:
        """Common query execution logic."""
        from ...widgets import VimMode

        if not self.current_connection or not self.current_adapter:
            self.notify("Not connected to a database", severity="warning")
            return

        query_input = self.query_one("#query-input", TextArea)
        query = query_input.text.strip()

        if not query:
            self.notify("No query to execute", severity="warning")
            return

        results_table = self.query_one("#results-table", DataTable)
        results_table.clear(columns=True)

        try:
            query_type = query.strip().upper().split()[0] if query.strip() else ""
            is_select_query = query_type in (
                "SELECT",
                "WITH",
                "SHOW",
                "DESCRIBE",
                "EXPLAIN",
                "PRAGMA",
            )

            if is_select_query:
                columns, rows = self.current_adapter.execute_query(
                    self.current_connection, query
                )
                row_count = len(rows)

                self._last_result_columns = columns
                self._last_result_rows = list(rows)
                self._last_result_row_count = row_count

                results_table.add_columns(*columns)
                for row in rows[:1000]:
                    str_row = tuple(str(v) if v is not None else "NULL" for v in row)
                    results_table.add_row(*str_row)

                self.notify(f"Query returned {row_count} rows")
            else:
                affected = self.current_adapter.execute_non_query(
                    self.current_connection, query
                )
                self._last_result_columns = ["Result"]
                self._last_result_rows = [(f"{affected} row(s) affected",)]
                self._last_result_row_count = 1

                results_table.add_column("Result")
                results_table.add_row(f"{affected} row(s) affected")
                self.notify(f"Query executed: {affected} row(s) affected")

            if self.current_config:
                from ...config import save_query_to_history

                save_query_to_history(self.current_config.name, query)

            if keep_insert_mode:
                self.vim_mode = VimMode.INSERT
                query_input.read_only = False
                query_input.focus()
                self._update_footer_bindings()
                self._update_status_bar()

        except Exception as e:
            self._last_result_columns = ["Error"]
            self._last_result_rows = [(str(e),)]
            self._last_result_row_count = 1

            results_table.add_column("Error")
            results_table.add_row(str(e))
            self.notify(f"Query error: {e}", severity="error")

    def action_clear_query(self) -> None:
        """Clear the query input."""
        query_input = self.query_one("#query-input", TextArea)
        query_input.text = ""

    def action_new_query(self) -> None:
        """Start a new query (clear input and results)."""
        query_input = self.query_one("#query-input", TextArea)
        query_input.text = ""
        results_table = self.query_one("#results-table", DataTable)
        results_table.clear(columns=True)

    def action_show_history(self) -> None:
        """Show query history for the current connection."""
        if not self.current_config:
            self.notify("Not connected to a database", severity="warning")
            return

        from ...config import load_query_history
        from ..screens import QueryHistoryScreen

        history = load_query_history(self.current_config.name)
        self.push_screen(
            QueryHistoryScreen(history, self.current_config.name),
            self._handle_history_result,
        )

    def _handle_history_result(self, result) -> None:
        """Handle the result from the history screen."""
        if result is None:
            return

        action, data = result
        if action == "select":
            query_input = self.query_one("#query-input", TextArea)
            query_input.text = data
        elif action == "delete":
            self._delete_history_entry(data)
            self.action_show_history()

    def _delete_history_entry(self, timestamp: str) -> None:
        """Delete a specific history entry by timestamp."""
        from ...config import delete_query_from_history

        delete_query_from_history(self.current_config.name, timestamp)
