# Security Strategy

## AI Security
- **Never trust AI-generated SQL**.

## SQL Safety
The future pipeline must be:
Natural language → LLM → SQL parser → SQL validation → read-only validation → schema validation → resource validation → execution.

Dangerous statements such as `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `CREATE`, and `TRUNCATE` must not be allowed in the read-only query system unless explicitly designed features require them in the future.

## API Keys
- Never place Gemini API keys in frontend code.
- Never commit `.env`.
- Use environment variables.

## Upload Security
Future upload functionality must consider:
- File size limits
- Allowed extensions
- Malformed SQLite databases
- Database integrity
- Temporary storage
- Isolation and cleanup

## Query Safety
Future execution must consider:
- Maximum execution time
- Maximum rows
- Maximum result size
- Resource exhaustion
- Expensive queries

## Information Disclosure
- Do not expose internal stack traces or secrets to end users.
