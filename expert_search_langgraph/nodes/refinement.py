import json
from typing import Dict, Any, List
import google.generativeai as genai
from ..state import ExpertSearchState

class GeminiQueryRefiner:
    def __init__(self, llm_model: genai.GenerativeModel, n_variants: int = 3):
        self.model = llm_model
        self.n_variants = n_variants

    def generate_variants(self, query: str) -> List[str]:
        prompt = (
            f"Rewrite this user search query into {self.n_variants} concise paraphrases.\n"
            "Return ONLY a JSON array of strings.\n\n"
            f"User query: \"{query}\""
        )
        resp = self.model.generate_content(prompt)
        text = resp.text.strip()
        try:
            arr = json.loads(text)
            return [v for v in arr if isinstance(v, str)][:self.n_variants]
        except json.JSONDecodeError:
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            return lines[:self.n_variants]


def check_and_refine(
    state: ExpertSearchState,
    refiner: GeminiQueryRefiner,
    quality_threshold: float = 0.5
) -> Dict[str, Any]:
    """Check quality and refine query if needed"""
    should_refine = (
        state["quality_score"] < quality_threshold 
        and state["iteration"] == 0
    )
    
    refined_queries = []
    if should_refine and refiner:
        refined_queries = refiner.generate_variants(state["query"])
    
    return {
        "should_refine": should_refine,
        "refined_queries": refined_queries,
        "iteration": state["iteration"] + 1
    }
