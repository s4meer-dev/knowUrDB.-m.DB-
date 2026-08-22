from typing import Any

from app.core.database import DatabaseProvider


class SchemaService:
    """
    Schema intelligence module to provide structured metadata about the database.
    """
    def __init__(self, db_provider: DatabaseProvider):
        self.db_provider = db_provider
        self._schema_cache = None

    def get_schema(self) -> dict[str, Any]:
        """
        Returns structured metadata about tables, columns, primary keys, and foreign keys.
        """
        if self._schema_cache:
            return self._schema_cache

        schema = {
            "tables": [],
            "relationships": []
        }

        conn = self.db_provider.get_connection()
        try:
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [row[0] for row in cursor.fetchall()]

            for table in tables:
                table_info = {
                    "name": table,
                    "columns": [],
                    "primary_key": None
                }
                
                # Get columns and primary key
                cursor.execute(f"PRAGMA table_info({table});")
                columns_info = cursor.fetchall()
                for col in columns_info:
                    col_name = col[1]
                    col_type = col[2]
                    is_pk = col[5] > 0
                    table_info["columns"].append({
                        "name": col_name,
                        "type": col_type
                    })
                    if is_pk:
                        # Assuming single column primary keys for simplicity
                        table_info["primary_key"] = col_name
                
                schema["tables"].append(table_info)

                # Get foreign keys (relationships)
                cursor.execute(f"PRAGMA foreign_key_list({table});")
                fks = cursor.fetchall()
                for fk in fks:
                    # fk is (id, seq, table, from, to, on_update, on_delete, match)
                    schema["relationships"].append({
                        "from_table": table,
                        "from_column": fk[3],
                        "to_table": fk[2],
                        "to_column": fk[4]
                    })

            self._schema_cache = schema
            return schema
        finally:
            conn.close()

    def get_table_names(self) -> list[str]:
        schema = self.get_schema()
        return [t["name"] for t in schema["tables"]]
