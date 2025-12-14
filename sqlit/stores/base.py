"""Base store class with common JSON file operations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Shared config directory
CONFIG_DIR = Path.home() / ".sqlit"


class JSONFileStore:
    """Base class for JSON file-backed stores.

    Provides common file I/O operations with error handling.
    """

    def __init__(self, file_path: Path):
        self._file_path = file_path

    @property
    def file_path(self) -> Path:
        """Get the store's file path."""
        return self._file_path

    def _ensure_dir(self) -> None:
        """Ensure the config directory exists."""
        self._file_path.parent.mkdir(parents=True, exist_ok=True)

    def _read_json(self) -> Any:
        """Read and parse JSON from file.

        Returns:
            Parsed JSON data, or None if file doesn't exist or is invalid.
        """
        if not self._file_path.exists():
            return None
        try:
            with open(self._file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, TypeError):
            return None

    def _write_json(self, data: Any) -> None:
        """Write data as JSON to file.

        Args:
            data: Data to serialize and write.
        """
        self._ensure_dir()
        with open(self._file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def exists(self) -> bool:
        """Check if the store file exists."""
        return self._file_path.exists()
