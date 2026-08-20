# AI Strategy

## Configuration and Isolation
The AI provider and model must be configurable through environment/configuration rather than hard-coded throughout the application. 
Use this conceptual configuration (via environment variables, not in code):
`AI_PROVIDER=gemini`
`AI_MODEL=<configured model>`

The application must isolate provider-specific implementation behind an abstract `AIProvider`. Future providers can be added without rewriting application services.

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

## AI Reliability and Prompt Design
To ensure AI reliability, the following must be implemented:
- **structured AI output**: Enforce specific response schemas.
- **schema-aware prompting**: Only supply the necessary schema.
- **prompt versioning**: Track changes to prompts over time.
- **model configuration**: Model parameters (temperature, etc.) must be configurable.
- **timeout handling**: Enforce strict timeouts for AI calls.
- **retry handling**: Implement robust retry logic for transient API failures.
- **rate-limit handling**: Respect AI provider rate limits.
- **malformed model response handling**: Safely parse and handle unexpected or malformed output.
- **SQL generation failure handling**: Gracefully handle cases where the AI fails to generate valid SQL.
- **SQL correction retry limits**: Set strict limits on AI self-correction attempts.
- **prevention of infinite AI correction loops**: Ensure the system cannot get stuck in an endless error-correction loop.
- **logging of AI request metadata without exposing secrets**: Log request durations, token usage, and status without exposing API keys or sensitive user data.

Future prompts must enforce:
- SQL dialect
- Read-only SQL
- Supplied-schema-only rule
- No invented tables
- No invented columns
- Structured output
- Concise explanation

## Security Boundary
**AI output is never itself a security boundary.** 
The backend remains strictly responsible for validating generated SQL.

## Error Correction
Future architecture:
Generated SQL → Execute → Database error → AI correction → Validate again → Execute again.
Set a strict maximum retry count. Do not create infinite AI correction loops.
