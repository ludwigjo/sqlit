"""Autocomplete mixin for SSMSTUI."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from textual.widgets import TextArea

if TYPE_CHECKING:
    from ...config import ConnectionConfig
    from ...widgets import VimMode


class AutocompleteMixin:
    """Mixin providing SQL autocomplete functionality."""

    # These attributes are defined in the main app class
    current_connection: Any
    current_config: "ConnectionConfig | None"
    current_adapter: Any
    vim_mode: "VimMode"
    _schema_cache: dict
    _autocomplete_visible: bool
    _autocomplete_items: list[str]
    _autocomplete_index: int
    _autocomplete_filter: str
    _autocomplete_just_applied: bool

    def _get_word_before_cursor(self, text: str, cursor_pos: int) -> tuple[str, str]:
        """Get the current word being typed and the context keyword before it."""
        if cursor_pos <= 0 or cursor_pos > len(text):
            return "", ""

        before_cursor = text[:cursor_pos]

        word_start = cursor_pos
        while word_start > 0 and before_cursor[word_start - 1] not in " \t\n,()[]":
            word_start -= 1
        current_word = before_cursor[word_start:cursor_pos]

        if "." in current_word:
            parts = current_word.rsplit(".", 1)
            table_name = parts[0].strip("[]")
            return parts[1] if len(parts) > 1 else "", f"column:{table_name}"

        context_text = before_cursor[:word_start].upper().strip()

        table_keywords = ["FROM", "JOIN", "INTO", "UPDATE", "TABLE"]
        for kw in table_keywords:
            if context_text.endswith(kw):
                return current_word, "table"

        if context_text.endswith("EXEC") or context_text.endswith("EXECUTE"):
            return current_word, "procedure"

        if context_text.endswith("SELECT") or context_text.endswith(","):
            return current_word, "column_or_table"

        return current_word, ""

    def _get_autocomplete_suggestions(self, word: str, context: str) -> list[str]:
        """Get autocomplete suggestions based on context."""
        suggestions = []

        if context == "table":
            suggestions = self._schema_cache["tables"] + self._schema_cache["views"]
        elif context == "procedure":
            suggestions = self._schema_cache["procedures"]
        elif context.startswith("column:"):
            table_name = context.split(":", 1)[1].lower()
            suggestions = self._schema_cache["columns"].get(table_name, [])
        elif context == "column_or_table":
            all_columns = []
            for cols in self._schema_cache["columns"].values():
                all_columns.extend(cols)
            suggestions = list(set(all_columns)) + self._schema_cache["tables"]

        if word:
            word_lower = word.lower()
            suggestions = [s for s in suggestions if s.lower().startswith(word_lower)]

        return suggestions[:50]

    def _show_autocomplete(self, suggestions: list[str], filter_text: str) -> None:
        """Show the autocomplete dropdown with suggestions."""
        from ...widgets import AutocompleteDropdown

        if not suggestions:
            self._hide_autocomplete()
            return

        dropdown = self.query_one("#autocomplete-dropdown", AutocompleteDropdown)
        dropdown.set_items(suggestions, filter_text)

        try:
            query_input = self.query_one("#query-input", TextArea)
            cursor_loc = query_input.cursor_location
            dropdown.styles.offset = (cursor_loc[1] + 2, cursor_loc[0] + 1)
        except Exception:
            pass

        dropdown.show()
        self._autocomplete_visible = True

    def _hide_autocomplete(self) -> None:
        """Hide the autocomplete dropdown."""
        from ...widgets import AutocompleteDropdown

        try:
            dropdown = self.query_one("#autocomplete-dropdown", AutocompleteDropdown)
            dropdown.hide()
            self._autocomplete_visible = False
        except Exception:
            pass

    def _apply_autocomplete(self) -> None:
        """Apply the selected autocomplete suggestion."""
        from ...widgets import AutocompleteDropdown

        dropdown = self.query_one("#autocomplete-dropdown", AutocompleteDropdown)
        selected = dropdown.get_selected()

        if not selected:
            self._hide_autocomplete()
            return

        self._autocomplete_just_applied = True

        query_input = self.query_one("#query-input", TextArea)
        text = query_input.text
        cursor_loc = query_input.cursor_location
        cursor_pos = self._location_to_offset(text, cursor_loc)

        word_start = cursor_pos
        while word_start > 0 and text[word_start - 1] not in " \t\n,()[]":
            word_start -= 1

        if word_start > 0 and text[word_start - 1] == ".":
            new_text = (
                text[:cursor_pos]
                + selected[len(text[word_start:cursor_pos]) :]
                + text[cursor_pos:]
            )
        else:
            new_text = text[:word_start] + selected + text[cursor_pos:]

        query_input.text = new_text

        new_cursor_pos = word_start + len(selected)
        new_loc = self._offset_to_location(new_text, new_cursor_pos)
        query_input.cursor_location = new_loc

        self._hide_autocomplete()

    def _location_to_offset(self, text: str, location: tuple) -> int:
        """Convert (row, col) location to text offset."""
        row, col = location
        lines = text.split("\n")
        offset = sum(len(lines[i]) + 1 for i in range(row))
        offset += col
        return min(offset, len(text))

    def _offset_to_location(self, text: str, offset: int) -> tuple:
        """Convert text offset to (row, col) location."""
        lines = text.split("\n")
        current_offset = 0
        for row, line in enumerate(lines):
            if current_offset + len(line) >= offset:
                return (row, offset - current_offset)
            current_offset += len(line) + 1
        return (len(lines) - 1, len(lines[-1]) if lines else 0)

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Handle text changes in the query editor for autocomplete."""
        from ...widgets import VimMode

        if event.text_area.id != "query-input":
            return

        if self._autocomplete_just_applied:
            self._autocomplete_just_applied = False
            self._hide_autocomplete()
            return

        if self.vim_mode != VimMode.INSERT:
            self._hide_autocomplete()
            return

        if not self.current_connection:
            return

        text = event.text_area.text
        cursor_loc = event.text_area.cursor_location
        cursor_pos = self._location_to_offset(text, cursor_loc)

        word, context = self._get_word_before_cursor(text, cursor_pos)

        if context:
            is_column_context = context.startswith("column:")
            if is_column_context or len(word) >= 1:
                suggestions = self._get_autocomplete_suggestions(word, context)
                if suggestions:
                    self._show_autocomplete(suggestions, word)
                else:
                    self._hide_autocomplete()
            else:
                self._hide_autocomplete()
        else:
            self._hide_autocomplete()

    def on_key(self, event) -> None:
        """Handle key events for autocomplete navigation."""
        from ...widgets import AutocompleteDropdown, VimMode

        if not self._autocomplete_visible:
            return

        dropdown = self.query_one("#autocomplete-dropdown", AutocompleteDropdown)

        if event.key == "down":
            dropdown.move_selection(1)
            event.prevent_default()
            event.stop()
        elif event.key == "up":
            dropdown.move_selection(-1)
            event.prevent_default()
            event.stop()
        elif event.key == "tab":
            if self.vim_mode == VimMode.INSERT and dropdown.filtered_items:
                self._apply_autocomplete()
                event.prevent_default()
                event.stop()
        elif event.key == "escape":
            self._hide_autocomplete()

    def _load_schema_cache(self) -> None:
        """Load database schema for autocomplete."""
        if not self.current_connection or not self.current_config or not self.current_adapter:
            return

        self._schema_cache = {
            "tables": [],
            "views": [],
            "columns": {},
            "procedures": [],
        }

        adapter = self.current_adapter

        try:
            if adapter.supports_multiple_databases:
                db = self.current_config.database
                if db and db.lower() not in ("", "master"):
                    databases = [db]
                else:
                    all_dbs = adapter.get_databases(self.current_connection)
                    system_dbs = {"master", "tempdb", "model", "msdb"}
                    databases = [d for d in all_dbs if d.lower() not in system_dbs]
            else:
                databases = [None]

            for database in databases:
                try:
                    tables = adapter.get_tables(self.current_connection, database)
                    for table_name in tables:
                        self._schema_cache["tables"].append(table_name)
                        if database:
                            full_name = f"{adapter.quote_identifier(database)}.{adapter.quote_identifier(table_name)}"
                            self._schema_cache["tables"].append(full_name)

                        columns = adapter.get_columns(self.current_connection, table_name, database)
                        self._schema_cache["columns"][table_name.lower()] = [c.name for c in columns]

                    views = adapter.get_views(self.current_connection, database)
                    for view_name in views:
                        self._schema_cache["views"].append(view_name)
                        if database:
                            full_name = f"{adapter.quote_identifier(database)}.{adapter.quote_identifier(view_name)}"
                            self._schema_cache["views"].append(full_name)

                        columns = adapter.get_columns(self.current_connection, view_name, database)
                        self._schema_cache["columns"][view_name.lower()] = [c.name for c in columns]

                    if adapter.supports_stored_procedures:
                        procedures = adapter.get_procedures(self.current_connection, database)
                        self._schema_cache["procedures"].extend(procedures)

                except Exception:
                    pass

            self._schema_cache["tables"] = list(dict.fromkeys(self._schema_cache["tables"]))
            self._schema_cache["views"] = list(dict.fromkeys(self._schema_cache["views"]))
            self._schema_cache["procedures"] = list(dict.fromkeys(self._schema_cache["procedures"]))

        except Exception as e:
            self.notify(f"Error loading schema: {e}", severity="warning")
