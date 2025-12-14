"""Value view screen for displaying cell contents."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Static, TextArea


class ValueViewScreen(ModalScreen):
    """Modal screen for viewing a single (potentially long) value."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("q", "dismiss", "Close"),
        Binding("y", "copy", "Copy"),
    ]

    CSS = """
    ValueViewScreen {
        align: center middle;
        background: transparent;
    }

    #value-dialog {
        width: 90;
        height: 70%;
        border: solid $primary;
        background: $surface;
        padding: 1 2;
    }

    #value-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #value-text {
        height: 1fr;
        border: solid $primary-darken-2;
    }

    #value-footer {
        height: 1;
        margin-top: 1;
        text-align: center;
        color: $text-muted;
    }
    """

    def __init__(self, value: str, title: str = "Value"):
        super().__init__()
        self.value = value
        self.title = title

    def compose(self) -> ComposeResult:
        with Container(id="value-dialog"):
            yield Static(self.title, id="value-title")
            yield TextArea(self.value, id="value-text", read_only=True)
            yield Static(r"[bold]\[Y][/] Copy  [bold]\[Esc][/] Close", id="value-footer")

    def on_mount(self) -> None:
        self.query_one("#value-text", TextArea).focus()

    def action_dismiss(self) -> None:
        self.dismiss(None)

    def action_copy(self) -> None:
        copied = getattr(self.app, "_copy_text", None)
        if callable(copied):
            copied(self.value)
        else:
            self.notify("Copy unavailable", timeout=2)
