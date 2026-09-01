import json
import logging
from typing import Any, Dict, List

from app.services.gemini_provider import GeminiProvider
from app.services.source_manager import SourceManager

logger = logging.getLogger(__name__)

class QueryRouter:
    """
    Intelligently routes a natural language query to the appropriate source(s).
    """
    def __init__(self, ai_provider: GeminiProvider, source_manager: SourceManager):
        self.ai = ai_provider
        self.source_manager = source_manager

    def route_query(self, question: str, explicit_source_ids: List[str] = None) -> Dict[str, Any]:
        """
        Determines the intent and the best source(s) to answer the query.
        Returns a dict with:
          - decision: SINGLE_SOURCE, MULTI_SOURCE, CLARIFICATION, UNRELATED
          - sources: list of selected source dictionaries
          - candidates: list of candidate source dictionaries (if clarification needed)
          - confidence: float score
          - reasoning: str
        """
        sources = self.source_manager.list_sources()
        
        # If user explicitly selected sources, only consider those
        if explicit_source_ids:
            sources = [s for s in sources if s.source_id in explicit_source_ids]
            
        if not sources:
            return {
                "decision": "UNRELATED",
                "sources": [],
                "candidates": [],
                "confidence": 1.0,
                "reasoning": "No sources available."
            }
            
        # Build a context of available sources for the LLM
        sources_context = []
        for s in sources:
            sources_context.append({
                "id": s.source_id,
                "name": s.name,
                "type": s.detected_format,
                "tables": s.table_count,
                "records": s.record_count
            })
            
        prompt = f"""
You are an intelligent query router for a multi-source data system.
You need to decide which source(s) should be used to answer the user's question.

Available Sources:
{json.dumps(sources_context, indent=2)}

User Question: "{question}"

Rules:
1. If the question is a general greeting or unrelated to any data (e.g., "what is the weather", "2+2", "write a poem"), decision is UNRELATED.
2. If the user explicitly asks about the available files/sources (e.g. "what files have I uploaded", "what sources are available"), decision is META.
3. If the question clearly refers to ONE specific source (by filename, context, or uniqueness of data requested), decision is SINGLE_SOURCE.
4. If the question explicitly asks to compare or join multiple specific sources, decision is MULTI_SOURCE.
5. IF THE QUESTION IS AMBIGUOUS and could apply to multiple sources equally (e.g. asking "what are the sales" when there are both 'sales_q1' and 'sales_q2'), YOU MUST NOT GUESS. The decision must be CLARIFICATION.
6. Return a confidence score between 0.0 and 1.0.

Return EXACTLY a JSON object with this structure (no markdown, no backticks):
{{
  "decision": "SINGLE_SOURCE" | "MULTI_SOURCE" | "CLARIFICATION" | "UNRELATED" | "META",
  "source_ids": ["id1", "id2"], // Empty if UNRELATED or META. If CLARIFICATION, list the possible candidates here.
  "confidence": 0.95,
  "reasoning": "Explain why you made this decision briefly."
}}
"""
        
        try:
            # We enforce strict JSON generation
            response_text = self.ai.generate_text(prompt)
            # Clean up potential markdown formatting
            if response_text.startswith("```json"):
                response_text = response_text[7:-3]
            elif response_text.startswith("```"):
                response_text = response_text[3:-3]
                
            decision_data = json.loads(response_text.strip())
            
            decision = decision_data.get("decision", "UNRELATED")
            source_ids = decision_data.get("source_ids", [])
            confidence = decision_data.get("confidence", 0.0)
            reasoning = decision_data.get("reasoning", "")
            
            selected_sources = []
            candidates = []
            
            for sid in source_ids:
                s = next((s for s in sources if s.source_id == sid), None)
                if s:
                    if decision == "CLARIFICATION":
                        candidates.append({"source_id": s.source_id, "name": s.name})
                    else:
                        selected_sources.append({
                            "source_id": s.source_id,
                            "name": s.name,
                            "type": s.detected_format,
                            "file_type": s.file_type
                        })
            
            return {
                "decision": decision,
                "sources": selected_sources,
                "candidates": candidates,
                "confidence": confidence,
                "reasoning": reasoning
            }
            
        except Exception as e:
            logger.error(f"Error in query router: {e}")
            # Safe fallback if AI parsing fails
            if len(sources) == 1:
                return {
                    "decision": "SINGLE_SOURCE",
                    "sources": [{"source_id": sources[0].source_id, "name": sources[0].name, "type": sources[0].detected_format, "file_type": sources[0].file_type}],
                    "candidates": [],
                    "confidence": 0.5,
                    "reasoning": "Fallback to only available source."
                }
            else:
                return {
                    "decision": "CLARIFICATION",
                    "sources": [],
                    "candidates": [{"source_id": s.source_id, "name": s.name} for s in sources],
                    "confidence": 0.0,
                    "reasoning": "Fallback required clarification due to multiple sources."
                }
