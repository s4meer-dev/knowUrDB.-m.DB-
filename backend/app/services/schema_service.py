from typing import Any

from app.core.database import DatabaseProvider
from app.models.schema import (
    ColumnInfo,
    DatabaseSchema,
    ForeignKeyInfo,
    SchemaSummary,
    TableInfo,
)


class SchemaService:
    """
    Schema intelligence module to provide structured metadata about the database.
    """

    def __init__(self, db_provider: DatabaseProvider):
        self.db_provider = db_provider
        self._schema_cache: DatabaseSchema | None = None

    def get_schema(self) -> DatabaseSchema:
        """
        Returns structured metadata about tables, columns, primary keys, and foreign keys.
        """
        if self._schema_cache:
            return self._schema_cache

        tables = []
        conn = self.db_provider.get_connection()
        try:
            cursor = conn.cursor()

            # Get all tables
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
            )
            table_names = [row[0] for row in cursor.fetchall()]

            for table_name in table_names:
                table_info = self._get_table_info_internal(cursor, table_name)
                tables.append(table_info)

            schema = DatabaseSchema(tables=tables)
            self._schema_cache = schema
            return schema
        finally:
            conn.close()

    def get_table_names(self) -> list[str]:
        schema = self.get_schema()
        return [t.name for t in schema.tables]

    def get_table_schema(self, table_name: str) -> TableInfo:
        """
        Returns schema information for a single table.
        Raises ValueError if the table does not exist or is internal.
        """
        if table_name.startswith("sqlite_"):
            raise ValueError(f"Access to internal table '{table_name}' is not allowed.")

        conn = self.db_provider.get_connection()
        try:
            cursor = conn.cursor()

            # Validate table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name = ?;",
                (table_name,),
            )
            if not cursor.fetchone():
                raise ValueError(f"Table '{table_name}' does not exist.")

            return self._get_table_info_internal(cursor, table_name)
        finally:
            conn.close()

    def _get_table_info_internal(self, cursor: Any, table_name: str) -> TableInfo:
        """Internal helper to fetch table schema using an existing cursor."""
        columns = []
        primary_keys = []

        # Get columns and primary key
        cursor.execute(f"PRAGMA table_info('{table_name}');")
        columns_info = cursor.fetchall()
        for col in columns_info:
            col_name = col[1]
            col_type = col[2]
            notnull = col[3]
            is_pk = col[5] > 0

            columns.append(
                ColumnInfo(
                    name=col_name,
                    data_type=col_type,
                    primary_key=is_pk,
                    nullable=not bool(notnull),
                )
            )

            if is_pk:
                primary_keys.append(col_name)

        # Get foreign keys (relationships)
        foreign_keys = []
        cursor.execute(f"PRAGMA foreign_key_list('{table_name}');")
        fks = cursor.fetchall()
        for fk in fks:
            # fk is (id, seq, table, from, to, on_update, on_delete, match)
            foreign_keys.append(
                ForeignKeyInfo(
                    source_column=fk[3], referenced_table=fk[2], referenced_column=fk[4]
                )
            )

        return TableInfo(
            name=table_name,
            columns=columns,
            primary_keys=primary_keys,
            foreign_keys=foreign_keys,
        )

    def get_schema_summary(self) -> SchemaSummary:
        """
        Returns a human-readable summary of the database schema.
        """
        schema = self.get_schema()

        if not schema.tables:
            return SchemaSummary(summary="The database is empty.")

        lines = ["Database contains the following tables:"]
        for table in schema.tables:
            col_names = [col.name for col in table.columns]
            lines.append(f"- {table.name} with columns {', '.join(col_names)}.")

        return SchemaSummary(summary=" ".join(lines))
