"""CLI command handlers for sqlit."""

from __future__ import annotations

import json

from .config import (
    AUTH_TYPE_LABELS,
    AuthType,
    ConnectionConfig,
    load_connections,
    save_connections,
)


def cmd_connection_list(args) -> int:
    """List all saved connections."""
    connections = load_connections()
    if not connections:
        print("No saved connections.")
        return 0

    print(f"{'Name':<20} {'Server':<30} {'Database':<15} {'Auth Type':<25}")
    print("-" * 90)
    for conn in connections:
        auth_label = AUTH_TYPE_LABELS.get(conn.get_auth_type(), conn.auth_type)
        print(
            f"{conn.name:<20} {conn.server:<30} {conn.database:<15} {auth_label:<25}"
        )
    return 0


def cmd_connection_create(args) -> int:
    """Create a new connection."""
    connections = load_connections()

    if any(c.name == args.name for c in connections):
        print(f"Error: Connection '{args.name}' already exists. Use 'edit' to modify it.")
        return 1

    try:
        auth_type = AuthType(args.auth_type)
    except ValueError:
        valid_types = ", ".join(t.value for t in AuthType)
        print(f"Error: Invalid auth type '{args.auth_type}'. Valid types: {valid_types}")
        return 1

    config = ConnectionConfig(
        name=args.name,
        server=args.server,
        port=args.port or "1433",
        database=args.database or "master",
        username=args.username or "",
        password=args.password or "",
        auth_type=auth_type.value,
        trusted_connection=(auth_type == AuthType.WINDOWS),
    )

    connections.append(config)
    save_connections(connections)
    print(f"Connection '{args.name}' created successfully.")
    return 0


def cmd_connection_edit(args) -> int:
    """Edit an existing connection."""
    connections = load_connections()

    conn_idx = None
    for i, c in enumerate(connections):
        if c.name == args.connection_name:
            conn_idx = i
            break

    if conn_idx is None:
        print(f"Error: Connection '{args.connection_name}' not found.")
        return 1

    conn = connections[conn_idx]

    if args.name:
        if args.name != conn.name and any(c.name == args.name for c in connections):
            print(f"Error: Connection '{args.name}' already exists.")
            return 1
        conn.name = args.name
    if args.server:
        conn.server = args.server
    if args.port:
        conn.port = args.port
    if args.database:
        conn.database = args.database
    if args.auth_type:
        try:
            auth_type = AuthType(args.auth_type)
            conn.auth_type = auth_type.value
            conn.trusted_connection = auth_type == AuthType.WINDOWS
        except ValueError:
            valid_types = ", ".join(t.value for t in AuthType)
            print(f"Error: Invalid auth type '{args.auth_type}'. Valid types: {valid_types}")
            return 1
    if args.username is not None:
        conn.username = args.username
    if args.password is not None:
        conn.password = args.password

    save_connections(connections)
    print(f"Connection '{conn.name}' updated successfully.")
    return 0


def cmd_connection_delete(args) -> int:
    """Delete a connection."""
    connections = load_connections()

    conn_idx = None
    for i, c in enumerate(connections):
        if c.name == args.connection_name:
            conn_idx = i
            break

    if conn_idx is None:
        print(f"Error: Connection '{args.connection_name}' not found.")
        return 1

    deleted = connections.pop(conn_idx)
    save_connections(connections)
    print(f"Connection '{deleted.name}' deleted successfully.")
    return 0


def cmd_query(args) -> int:
    """Execute a SQL query against a connection."""
    try:
        import pyodbc
    except ImportError:
        print("Error: pyodbc is not installed. Run: pip install pyodbc")
        return 1

    connections = load_connections()

    conn = None
    for c in connections:
        if c.name == args.connection:
            conn = c
            break

    if conn is None:
        print(f"Error: Connection '{args.connection}' not found.")
        return 1

    if args.database:
        conn.database = args.database

    if args.query:
        query = args.query
    elif args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                query = f.read()
        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found.")
            return 1
        except IOError as e:
            print(f"Error reading file: {e}")
            return 1
    else:
        print("Error: Either --query or --file must be provided.")
        return 1

    try:
        conn_str = conn.get_connection_string()
        db_conn = pyodbc.connect(conn_str, timeout=10)
        cursor = db_conn.cursor()
        cursor.execute(query)

        if cursor.description:
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

            if args.format == "csv":
                print(",".join(columns))
                for row in rows:
                    print(",".join(str(val) if val is not None else "" for val in row))
            elif args.format == "json":
                result = []
                for row in rows:
                    result.append(
                        dict(
                            zip(
                                columns,
                                [val if val is not None else None for val in row],
                            )
                        )
                    )
                print(json.dumps(result, indent=2, default=str))
            else:
                col_widths = [len(col) for col in columns]
                for row in rows:
                    for i, val in enumerate(row):
                        col_widths[i] = max(
                            col_widths[i], len(str(val) if val is not None else "NULL")
                        )

                header = " | ".join(
                    col.ljust(col_widths[i]) for i, col in enumerate(columns)
                )
                print(header)
                print("-" * len(header))

                for row in rows:
                    row_str = " | ".join(
                        (str(val) if val is not None else "NULL").ljust(col_widths[i])
                        for i, val in enumerate(row)
                    )
                    print(row_str)

            print(f"\n({len(rows)} row(s) returned)")
        else:
            print(f"Query executed successfully. Rows affected: {cursor.rowcount}")

        db_conn.commit()
        cursor.close()
        db_conn.close()
        return 0

    except pyodbc.Error as e:
        print(f"Database error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1
