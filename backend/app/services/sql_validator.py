import re


class SQLSafetyError(Exception):
    pass

class SQLValidator:
    """
    Validates SQL queries to ensure they are safe for read-only execution.
    """
    
    # List of dangerous keywords that mutate state or affect schema
    FORBIDDEN_KEYWORDS = [
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", 
        "REPLACE", "ATTACH", "DETACH", "PRAGMA", "VACUUM", "BEGIN", 
        "COMMIT", "ROLLBACK", "SAVEPOINT", "RELEASE", "GRANT", "REVOKE"
    ]

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
        if not (cleaned_sql.startswith("SELECT") or cleaned_sql.startswith("WITH")):
            raise SQLSafetyError("Only SELECT or WITH queries are allowed.")

        # 2. Reject multiple statements
        # We check if there's a semicolon followed by any non-whitespace character
        if re.search(r";\s*\S", sql):
            raise SQLSafetyError("Multiple SQL statements are not allowed.")

        # 3. Reject forbidden keywords
        # Using word boundaries to avoid matching keywords inside valid identifiers/strings (partially)
        # However, a simple regex is safer for a strict sandbox
        for keyword in cls.FORBIDDEN_KEYWORDS:
            # Check if the keyword exists as a whole word
            pattern = rf"\b{keyword}\b"
            if re.search(pattern, cleaned_sql):
                raise SQLSafetyError(f"Dangerous SQL pattern detected: {keyword} is not allowed.")

