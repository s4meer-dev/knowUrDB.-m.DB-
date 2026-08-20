# Decision Log

**Decision:** Use SQLite initially.  
**Reason:** Simple deployment and local database portability.

**Decision:** Use FastAPI.  
**Reason:** Strong Python ecosystem, async support, API development, Pydantic integration.

**Decision:** Use Gemini API.  
**Reason:** Strong current Google model ecosystem and good fit for natural-language-to-SQL reasoning.

**Decision:** Keep AI provider abstract.  
**Reason:** Avoid vendor lock-in.

**Decision:** Validate AI-generated SQL server-side.  
**Reason:** LLM output cannot be trusted as a security boundary.
