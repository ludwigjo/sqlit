#!/usr/bin/env python3
"""sqlit - A terminal UI for SQL Server."""

from __future__ import annotations

import argparse
import sys

from .config import AuthType


def main() -> int:
    """Entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="sqlit",
        description="A terminal UI for SQL Server",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Connection commands
    conn_parser = subparsers.add_parser("connection", help="Manage connections")
    conn_subparsers = conn_parser.add_subparsers(
        dest="conn_command", help="Connection commands"
    )

    # connection list
    conn_subparsers.add_parser("list", help="List all saved connections")

    # connection create
    create_parser = conn_subparsers.add_parser("create", help="Create a new connection")
    create_parser.add_argument("--name", "-n", required=True, help="Connection name")
    create_parser.add_argument("--server", "-s", required=True, help="Server address")
    create_parser.add_argument("--port", "-P", default="1433", help="Port (default: 1433)")
    create_parser.add_argument(
        "--database", "-d", default="", help="Database (empty = browse all databases)"
    )
    create_parser.add_argument(
        "--auth-type",
        "-a",
        default="windows",
        choices=[t.value for t in AuthType],
        help="Authentication type (default: windows)",
    )
    create_parser.add_argument("--username", "-u", help="Username")
    create_parser.add_argument("--password", "-p", help="Password")

    # connection edit
    edit_parser = conn_subparsers.add_parser("edit", help="Edit an existing connection")
    edit_parser.add_argument("connection_name", help="Name of connection to edit")
    edit_parser.add_argument("--name", "-n", help="New connection name")
    edit_parser.add_argument("--server", "-s", help="Server address")
    edit_parser.add_argument("--port", "-P", help="Port")
    edit_parser.add_argument("--database", "-d", help="Database")
    edit_parser.add_argument(
        "--auth-type",
        "-a",
        choices=[t.value for t in AuthType],
        help="Authentication type",
    )
    edit_parser.add_argument("--username", "-u", help="Username")
    edit_parser.add_argument("--password", "-p", help="Password")

    # connection delete
    delete_parser = conn_subparsers.add_parser("delete", help="Delete a connection")
    delete_parser.add_argument("connection_name", help="Name of connection to delete")

    # query command
    query_parser = subparsers.add_parser("query", help="Execute a SQL query")
    query_parser.add_argument(
        "--connection", "-c", required=True, help="Connection name to use"
    )
    query_parser.add_argument(
        "--database", "-d", help="Database to query (overrides connection default)"
    )
    query_parser.add_argument("--query", "-q", help="SQL query to execute")
    query_parser.add_argument("--file", "-f", help="SQL file to execute")
    query_parser.add_argument(
        "--format",
        "-o",
        default="table",
        choices=["table", "csv", "json"],
        help="Output format (default: table)",
    )

    args = parser.parse_args()

    # No command = launch TUI
    if args.command is None:
        from .app import SSMSTUI

        app = SSMSTUI()
        app.run()
        return 0

    # Import commands lazily to speed up --help
    from .commands import (
        cmd_connection_create,
        cmd_connection_delete,
        cmd_connection_edit,
        cmd_connection_list,
        cmd_query,
    )

    # Handle connection commands
    if args.command == "connection":
        if args.conn_command == "list":
            return cmd_connection_list(args)
        elif args.conn_command == "create":
            return cmd_connection_create(args)
        elif args.conn_command == "edit":
            return cmd_connection_edit(args)
        elif args.conn_command == "delete":
            return cmd_connection_delete(args)
        else:
            conn_parser.print_help()
            return 1

    # Handle query command
    if args.command == "query":
        return cmd_query(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
