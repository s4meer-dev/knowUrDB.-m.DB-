import re


class SQLSafetyError(Exception):
    pass


class SQLValidator:
    """
    Validates SQL queries to ensure they are safe for read-only execution.
    """

    @classmethod
    def validate_against_db(cls, sql: str, db_provider) -> None:
        """
        Validates the given SQL string against the actual database schema using EXPLAIN.
        Raises QueryExecutionError (via sqlite3.OperationalError) if tables/columns don't exist.
        """
        conn = db_provider.get_connection()
        try:
            # Running EXPLAIN parses the query and generates bytecode, checking if tables/columns exist.
            # It does not execute the query, making it safe.
            conn.execute(f"EXPLAIN {sql}")
        finally:
            conn.close()

    # List of dangerous keywords that mutate state or affect schema
    FORBIDDEN_KEYWORDS = frozenset(
        [
            "INSERT",
            "UPDATE",
            "DELETE",
            "DROP",
            "ALTER",
            "CREATE",
            "REPLACE",
            "ATTACH",
            "DETACH",
            "PRAGMA",
            "VACUUM",
            "BEGIN",
            "COMMIT",
            "ROLLBACK",
            "SAVEPOINT",
            "RELEASE",
            "GRANT",
            "REVOKE",
        ]
    )

    @classmethod
    def validate(cls, sql: str) -> None:
        """
        Validates the given SQL string.
        Raises SQLSafetyError if it fails validation.
        """
        if not sql or not sql.strip():
            raise SQLSafetyError("SQL query is empty.")

        cleaned_sql = sql.strip().upper()

        # 1. Must start with SELECT or WITH
        if not cleaned_sql.startswith(("SELECT", "WITH")):
            raise SQLSafetyError("Only SELECT or WITH queries are allowed.")

        # 2. Reject multiple statements
        # We check if there's a semicolon followed by any non-whitespace character
        if re.search(r";\s*\S", sql):
            raise SQLSafetyError("Multiple SQL statements are not allowed.")

        # 3. Reject forbidden keywords
        # Remove string literals to avoid false positives on data like 'drop_rate' or 'insert'
        # A string literal in SQL starts and ends with a single quote.
        sql_no_strings = re.sub(r"'(?:''|[^'])*'", "''", cleaned_sql)
        
        for keyword in cls.FORBIDDEN_KEYWORDS:
            # Check if the keyword exists as a whole word
            pattern = rf"\b{keyword}\b"
            if re.search(pattern, sql_no_strings):
                raise SQLSafetyError(
                    f"Dangerous SQL pattern detected: {keyword} is not allowed."
                )
