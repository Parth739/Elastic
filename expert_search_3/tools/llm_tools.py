import httpx
import json
import asyncio
import re
from typing import List, Dict, Any, Optional, Tuple
from config.settings import LLM_API_URL, LLM_MODEL, LLM_TIMEOUT
import logging
from models.schemas import ReasoningTrace
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.api_url = LLM_API_URL
        self.model = LLM_MODEL
        self.timeout = LLM_TIMEOUT
    
    async def generate_with_reasoning(self, prompt: str, stream: bool = False) -> Tuple[str, str]:
        """Generate text with explicit reasoning"""
        reasoning_prompt = f"""
{prompt}

Please think step-by-step before providing your final answer. Show your reasoning process.
Format your response as:
<reasoning>
[Your step-by-step thought process here]
</reasoning>

<answer>
[Your final answer here]
</answer>
"""
        
        full_response = await self.generate(reasoning_prompt, stream)
        
        reasoning = ""
        answer = ""
        
        if "<reasoning>" in full_response and "</reasoning>" in full_response:
            reasoning_match = re.search(r'<reasoning>(.*?)</reasoning>', full_response, re.DOTALL)
            if reasoning_match:
                reasoning = reasoning_match.group(1).strip()
        
        if "<answer>" in full_response and "</answer>" in full_response:
            answer_match = re.search(r'<answer>(.*?)</answer>', full_response, re.DOTALL)
            if answer_match:
                answer = answer_match.group(1).strip()
        else:
            answer = full_response
            reasoning = "Direct response without explicit reasoning"
        
        return answer, reasoning
    
    async def generate(self, prompt: str, stream: bool = False) -> str:
        """Original generate method"""
        try:
            async with httpx.AsyncClient(verify=False, timeout=self.timeout) as client:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": stream
                }
                
                logger.info(f"Sending request to LLM: {self.api_url}")
                response = await client.post(self.api_url, json=payload)
                
                if response.status_code != 200:
                    logger.error(f"LLM API error: {response.status_code} - {response.text}")
                    return self._fallback_response(prompt)
                
                if stream:
                    full_response = ""
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                if "response" in data:
                                    full_response += data["response"]
                            except json.JSONDecodeError:
                                continue
                    return full_response
                else:
                    return response.json().get("response", "")
                    
        except Exception as e:
            logger.error(f"Error calling LLM API: {e}")
            return self._fallback_response(prompt)
    
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """Original analyze method for backward compatibility"""
        analysis, _ = await self.analyze_query_with_reasoning(query)
        return analysis
    
    async def analyze_query_with_reasoning(self, query: str) -> Tuple[Dict[str, Any], str]:
        """Analyze query with visible reasoning"""
        prompt = f"""
Analyze the following user query using **both expert search strategies**: 

1. **Direct Expert Search** — where the user directly asks for a specific expert.
2. **Project-Based Expert Search** — where the user describes a task, project, or need, and we infer the kind of expert required.

Query: "{query}"

Think through:
- What is the user looking for?
- What are the key requirements and constraints?
- What expertise or domains are relevant?
- Are there signals for geography, experience, or other filters?

Output a JSON object with separate analysis for both strategies:

{{
    "direct_expert_strategy": {{
        "is_applicable": true/false,
        "key_requirements": [],
        "expertise_areas": [],
        "geographical_focus": [],
        "experience_level": null or number,
        "summary": "Why/how this strategy applies or doesn't apply"
    }},
    "project_based_strategy": {{
        "is_applicable": true/false,
        "project_needs": "Summary of the project or task",
        "required_expert_profile": {{
            "expertise_areas": [],
            "geographical_focus": [],
            "experience_level": null or number
        }},
        "summary": "Why/how this strategy applies or doesn't apply"
    }},
    "final_notes": "Optional high-level insights or suggested next steps"
}}
"""
        
        response, reasoning = await self.generate_with_reasoning(prompt)
        
        try:
            analysis = json.loads(response)
            return analysis, reasoning
        except:
            query_lower = query.lower()
            if any(word in query_lower for word in ["project", "agenda", "initiative", "implementing", "building"]):
                query_type = "project_based"
                reasoning = "Query contains project-related keywords"
            else:
                query_type = "direct_expert"
                reasoning = "Query appears to be a direct search for experts"
            
            return {
                "query_type": query_type,
                "key_requirements": query.split()[:5],
                "reasoning_summary": reasoning
            }, reasoning
    
    async def enhance_query(self, query: str, count: int = 3) -> List[str]:
        """Original enhance method for backward compatibility"""
        enhanced, _ = await self.enhance_query_with_reasoning(query, count)
        return enhanced
    
    async def enhance_query_with_reasoning(self, query: str, count: int = 3) -> Tuple[List[str], str]:
        """Generate enhanced queries with reasoning"""
        prompt = f"""
Generate {count} enhanced search queries based on this original query.

Original query: "{query}"

Consider:
- What variations might capture different aspects of the expertise needed?
- What related terms or synonyms could improve search results?
- How can we make the query more specific while maintaining intent?

Return only the enhanced queries, one per line, after your reasoning.
"""
        
        response, reasoning = await self.generate_with_reasoning(prompt)
        
        queries = [q.strip() for q in response.split('\n') if q.strip() and not q.startswith('-')][:count]
        
        if not queries:
            queries = [
                query,
                f"experienced {query}",
                f"senior {query} specialist"
            ]
            reasoning = "Using default query variations"
        
        return queries, reasoning
    
    async def extract_keywords(self, query: str) -> List[str]:
        """Original extract keywords method for backward compatibility"""
        keywords, _ = await self.extract_keywords_with_reasoning(query)
        return keywords
    
    async def extract_keywords_with_reasoning(self, query: str) -> Tuple[List[str], str]:
        """Extract keywords with reasoning"""
        prompt = f"""
Extract important keywords from this query for search purposes.

Query: "{query}"

Think about:
- What are the core technical terms?
- What synonyms or related concepts should we include?
- Which words are most important for finding relevant experts?

Return ONLY comma-separated keywords after your reasoning.
"""
        
        response, reasoning = await self.generate_with_reasoning(prompt)
        
        keywords = []
        if response:
            response = re.sub(r'[^\w\s,-]', '', response)
            keywords = [k.strip() for k in response.split(',') if k.strip() and len(k.strip()) > 2][:15]
        
        if not keywords:
            words = query.lower().split()
            stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'find', 'need', 'want'}
            keywords = [w for w in words if w not in stopwords and len(w) > 2][:10]
            reasoning = "Used basic keyword extraction due to parsing issues"

        print(keywords)
        return keywords, reasoning
    
    async def generate_expert_profile(self, project_description: str) -> str:
        """Generate ideal expert profile based on project description"""
        prompt = f"""
Based on this project description, describe the ideal expert profile.
Include required skills, experience, and expertise areas.

Project: {project_description}

Write a concise expert profile description (2-3 sentences) that can be used for searching.
Focus on key skills and experience needed.
"""
        
        response = await self.generate(prompt)
        
        if response == "LLM service unavailable" or not response:
            return f"Expert with experience in: {project_description[:100]}..."
        
        return response
    
    async def rerank_results(self, query: str, results: List[Dict]) -> List[Dict]:
        """Original rerank method for backward compatibility"""
        reranked, _ = await self.rerank_with_reasoning(query, results)
        return reranked
    
    async def rerank_with_reasoning(self, query: str, results: List[Dict]) -> Tuple[List[Dict], str]:
        """Rerank results with better parsing"""
        if not results:
            return results, "No results to rerank"
        
        results_to_rank = results[:10]
        
        results_text = ""
        for i, r in enumerate(results_to_rank, 1):
            headline = r.get('headline', 'No headline')[:80]
            bio = r.get('bio', '')[:80]
            results_text += f"{i}. {headline} | {bio}...\n"
        
        prompt = f"""
Rerank these experts based on relevance to: "{query}"

Experts:
{results_text}

Instructions:
1. Consider relevance to the query
2. Return ONLY numbers separated by commas
3. Example output: 3,1,5,2,4,7,6,8,9,10
4. Do not include any other text

Output:
"""
        
        try:
            response = await self.generate(prompt)
            
            cleaned = re.sub(r'[^\d,]', '', response.strip())
            
            if cleaned:
                numbers = [int(n) for n in cleaned.split(',') if n]
                valid_numbers = [n-1 for n in numbers if 1 <= n <= len(results_to_rank)]
                
                if valid_numbers:
                    reranked = []
                    seen = set()
                    
                    for idx in valid_numbers:
                        if idx not in seen and idx < len(results_to_rank):
                            reranked.append(results_to_rank[idx])
                            seen.add(idx)
                    
                    for i, item in enumerate(results_to_rank):
                        if i not in seen:
                            reranked.append(item)
                    
                    if len(results) > 10:
                        reranked.extend(results[10:])
                    
                    reasoning = f"Successfully reranked {len(valid_numbers)} experts based on relevance to query"
                    return reranked, reasoning
        
        except Exception as e:
            logger.error(f"Reranking error: {e}")
        
        query_words = set(query.lower().split())
        scored_results = []
        
        for item in results:
            score = 0
            text = f"{item.get('headline', '')} {item.get('bio', '')}".lower()
            for word in query_words:
                if word in text:
                    score += 1
            scored_results.append((score, item))
        
        scored_results.sort(key=lambda x: x[0], reverse=True)
        reranked = [item for score, item in scored_results]
        
        return reranked, "Reranked using keyword matching due to LLM parsing issues"
    
    async def evaluate_expert_relevance(self, expert: Dict, query: str) -> str:
        """Generate explanation for why an expert is relevant"""
        prompt = f"""
Explain in one sentence why this expert is relevant to the query.

Query: {query}
Expert: {expert.get('headline', 'No headline')} - {expert.get('bio', '')[:200]}

Be specific and concise.
"""
        
        response = await self.generate(prompt)
        return response if response else "Matches query requirements"
    
    def _fallback_response(self, prompt: str) -> str:
        """Fallback responses when LLM is unavailable"""
        if "analyze" in prompt.lower():
            return json.dumps({
                "query_type": "direct_expert",
                "key_requirements": ["expert", "search"],
                "expertise_areas": [],
                "geographical_focus": [],
                "experience_level": None
            })
        elif "enhance" in prompt.lower():
            return prompt.split("Original query:")[-1].strip()
        elif "keywords" in prompt.lower():
            words = prompt.lower().split()
            keywords = [w for w in words if len(w) > 4][:5]
            return ", ".join(keywords)
        elif "expert profile" in prompt.lower():
            return "Expert with relevant experience in the described project area"
        else:
            return "LLM service unavailable"
