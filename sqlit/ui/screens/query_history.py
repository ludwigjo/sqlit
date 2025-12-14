"""Query history screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option


class QueryHistoryScreen(ModalScreen):
    """Modal screen for query history selection."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "select", "Select"),
        Binding("d", "delete", "Delete"),
    ]

    CSS = """
    QueryHistoryScreen {
        align: center middle;
        background: transparent;
    }

    #history-dialog {
        width: 90;
        height: 80%;
        border: solid $primary;
        background: $surface;
        padding: 1 2;
    }

    #history-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #history-list {
        height: 1fr;
        background: $surface;
        border: solid $primary-darken-2;
        padding: 0;
    }

    #history-list > .option-list--option {
        padding: 0 1;
    }

    #history-preview {
        height: 8;
        background: $surface-darken-1;
        border: solid $primary-darken-2;
        padding: 1;
        margin-top: 1;
        overflow-y: auto;
    }

    #history-footer {
        margin-top: 1;
        text-align: center;
        color: $text-muted;
    }
    """

    def __init__(self, history: list, connection_name: str):
        super().__init__()
        self.history = history  # list of QueryHistoryEntry
        self.connection_name = connection_name

    def compose(self) -> ComposeResult:
        from datetime import datetime

        with Container(id="history-dialog"):
            yield Static(f"Query History - {self.connection_name}", id="history-title")

            options = []
            for entry in self.history:
                # Format timestamp nicely
                try:
                    dt = datetime.fromisoformat(entry.timestamp)
                    time_str = dt.strftime("%Y-%m-%d %H:%M")
                except (ValueError, AttributeError):
                    time_str = "Unknown"

                # Truncate query for display
                query_preview = entry.query.replace("\n", " ")[:50]
                if len(entry.query) > 50:
                    query_preview += "..."

                options.append(Option(f"[dim]{time_str}[/] {query_preview}", id=entry.timestamp))

            if options:
                yield OptionList(*options, id="history-list")
            else:
                yield Static("No query history for this connection", id="history-list")

            yield Static("", id="history-preview")
            yield Static(r"[bold]\[Enter][/] Select  [bold]\[D][/] Delete  [bold]\[Esc][/] Cancel", id="history-footer")

    def on_mount(self) -> None:
        try:
            option_list = self.query_one("#history-list", OptionList)
            option_list.focus()
            if self.history:
                self._update_preview(0)
        except Exception:
            pass

    def on_option_list_option_highlighted(self, event) -> None:
        if event.option_list.id == "history-list":
            idx = event.option_list.highlighted
            if idx is not None:
                self._update_preview(idx)

    def _update_preview(self, idx: int) -> None:
        if idx < len(self.history):
            preview = self.query_one("#history-preview", Static)
            preview.update(self.history[idx].query)

    def action_select(self) -> None:
        if not self.history:
            self.dismiss(None)
            return

        try:
            option_list = self.query_one("#history-list", OptionList)
            idx = option_list.highlighted
            if idx is not None and idx < len(self.history):
                self.dismiss(("select", self.history[idx].query))
            else:
                self.dismiss(None)
        except Exception:
            self.dismiss(None)

    def on_option_list_option_selected(self, event) -> None:
        if event.option_list.id == "history-list":
            idx = event.option_list.highlighted
            if idx is not None and idx < len(self.history):
                self.dismiss(("select", self.history[idx].query))

    def action_delete(self) -> None:
        """Delete the selected history entry."""
        if not self.history:
            return

        try:
            option_list = self.query_one("#history-list", OptionList)
            idx = option_list.highlighted
            if idx is not None and idx < len(self.history):
                # Remove from history and refresh
                entry = self.history[idx]
                self.dismiss(("delete", entry.timestamp))
        except Exception:
            pass

    def action_cancel(self) -> None:
        self.dismiss(None)
