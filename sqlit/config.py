"""Configuration management for sqlit."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class AuthType(Enum):
    """Authentication types for SQL Server connections."""

    WINDOWS = "windows"
    SQL_SERVER = "sql"
    AD_PASSWORD = "ad_password"
    AD_INTERACTIVE = "ad_interactive"
    AD_INTEGRATED = "ad_integrated"


AUTH_TYPE_LABELS = {
    AuthType.WINDOWS: "Windows Authentication",
    AuthType.SQL_SERVER: "SQL Server Authentication",
    AuthType.AD_PASSWORD: "Microsoft Entra Password",
    AuthType.AD_INTERACTIVE: "Microsoft Entra MFA",
    AuthType.AD_INTEGRATED: "Microsoft Entra Integrated",
}


@dataclass
class ConnectionConfig:
    """SQL Server connection configuration."""

    name: str
    server: str
    port: str = "1433"
    database: str = "master"
    username: str = ""
    password: str = ""
    auth_type: str = "windows"
    driver: str = "ODBC Driver 18 for SQL Server"
    trusted_connection: bool = True  # Legacy field for backwards compatibility

    def __post_init__(self):
        """Handle backwards compatibility with old configs."""
        if self.auth_type == "windows" and not self.trusted_connection and self.username:
            self.auth_type = "sql"

    def get_auth_type(self) -> AuthType:
        """Get the AuthType enum value."""
        try:
            return AuthType(self.auth_type)
        except ValueError:
            return AuthType.WINDOWS

    def get_connection_string(self) -> str:
        """Build the connection string."""
        server_with_port = self.server
        if self.port and self.port != "1433":
            server_with_port = f"{self.server},{self.port}"

        base = (
            f"DRIVER={{{self.driver}}};"
            f"SERVER={server_with_port};"
            f"DATABASE={self.database};"
            f"TrustServerCertificate=yes;"
        )

        auth = self.get_auth_type()

        if auth == AuthType.WINDOWS:
            return base + "Trusted_Connection=yes;"
        elif auth == AuthType.SQL_SERVER:
            return base + f"UID={self.username};PWD={self.password};"
        elif auth == AuthType.AD_PASSWORD:
            return (
                base
                + f"Authentication=ActiveDirectoryPassword;"
                f"UID={self.username};PWD={self.password};"
            )
        elif auth == AuthType.AD_INTERACTIVE:
            return (
                base + f"Authentication=ActiveDirectoryInteractive;" f"UID={self.username};"
            )
        elif auth == AuthType.AD_INTEGRATED:
            return base + "Authentication=ActiveDirectoryIntegrated;"

        return base + "Trusted_Connection=yes;"


CONFIG_DIR = Path.home() / ".sqlit"
CONFIG_PATH = CONFIG_DIR / "connections.json"
SETTINGS_PATH = CONFIG_DIR / "settings.json"


def load_settings() -> dict:
    """Load app settings from config file."""
    if not SETTINGS_PATH.exists():
        return {}
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, TypeError):
        return {}


def save_settings(settings: dict) -> None:
    """Save app settings to config file."""
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)


def load_connections() -> list[ConnectionConfig]:
    """Load saved connections from config file."""
    if not CONFIG_PATH.exists():
        return []
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [ConnectionConfig(**conn) for conn in data]
    except (json.JSONDecodeError, TypeError):
        return []


def save_connections(connections: list[ConnectionConfig]) -> None:
    """Save connections to config file."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump([vars(c) for c in connections], f, indent=2)
