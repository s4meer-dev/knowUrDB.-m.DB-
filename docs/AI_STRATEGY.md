# AI Strategy

## Initial Approach
Schema-aware Text-to-SQL.
The LLM should receive:
- Database dialect
- Relevant schema
- Table names
- Column names
- Data types
- Primary keys
- Foreign keys
- Relationships
- User question
- Relevant conversation context (when implemented)

The LLM should NOT receive the entire database contents by default.

## Prompt Design
Future prompts must enforce:
- SQL dialect
- Read-only SQL
- Supplied-schema-only rule
- No invented tables
- No invented columns
- Structured output
- Concise explanation

## Error Correction
Future architecture:
Generated SQL → Execute → Database error → AI correction → Validate again → Execute again.
Set a strict maximum retry count. Do not create infinite AI correction loops.
