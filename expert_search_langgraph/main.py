import os
import json
import pandas as pd
from dotenv import load_dotenv
import google.generativeai as genai

from tools.vector_search import StructuredVectorSearchTool, AgendaVectorSearchTool
from tools.keyword_search import StructuredKeywordSearchTool, AgendaKeywordSearchTool
from tools.reranker import AgendaResultsReranker
from nodes.refinement import GeminiQueryRefiner
from graph import create_expert_search_graph
from state import ExpertSearchState

# Configure Gemini
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
llm = genai.GenerativeModel("models/gemini-1.5-flash")

def extract_agenda_docs(df: pd.DataFrame):
    """Extract agenda documents from project data"""
    docs = []
    for _, row in df.iterrows():
        try:
            eid = int(row["expert_id"])
        except (KeyError, ValueError):
            continue

        bio = row.get("expert_bio", "") or ""
        headline = row.get("expert_headline", "") or ""
        summary = row.get("expert_work_summary", "") or ""
        raw = row.get("project_agenda_responses", "[]")
        
        try:
            qa_list = json.loads(raw)
        except json.JSONDecodeError:
            continue

        for idx, qa in enumerate(qa_list):
            q = (qa.get("question") or "").strip()
            a = (qa.get("answer") or "").strip()
            text = f"{q} {a}".strip()
            if not text:
                continue
            
            doc_id = eid * 1000 + idx
            docs.append({
                "_id": doc_id,
                "expert_id": eid,
                "expert_name": row.get("expert_name", "") or "",
                "expert_bio": bio,
                "expert_headline": headline,
                "expert_work_summary": summary,
                "text": text
            })
    return docs


def main():
    # Load data
    normal_df = pd.read_csv("experts_202505291522.csv", encoding="utf8")
    proj_df = pd.read_csv("project_expert_data.csv", encoding="latin1")

    # Initialize tools
    print("Initializing search tools...")
    norm_vec_tool = StructuredVectorSearchTool(collection_name="norm_experts")
    norm_vec_tool.add_documents(normal_df)
    
    norm_kw_tool = StructuredKeywordSearchTool()
    norm_kw_tool.add_documents(normal_df)

    proj_docs = extract_agenda_docs(proj_df)
    proj_vec_tool = AgendaVectorSearchTool(collection_name="agenda_responses")
    proj_vec_tool.add_documents(proj_docs)
    
    proj_kw_tool = AgendaKeywordSearchTool()
    proj_kw_tool.add_documents(proj_docs)

    # Setup reranker & refiner
    reranker = AgendaResultsReranker(alpha=0.6)
    refiner = GeminiQueryRefiner(llm, n_variants=3)

    # Create the LangGraph
    print("Building LangGraph...")
    graph = create_expert_search_graph(
        normal_vec_tool=norm_vec_tool,
        normal_kw_tool=norm_kw_tool,
        proj_vec_tool=proj_vec_tool,
        proj_kw_tool=proj_kw_tool,
        reranker=reranker,
        refiner=refiner,
        initial_k=10,
        final_n=5,
        quality_threshold=0.5
    )

    # Interactive loop
    print("\nExpert Search Ready!")
    while True:
        query = input("\nEnter your query (or 'exit'): ").strip()
        if query.lower() in ("exit", "quit"):
            break

        # Initialize state
        initial_state = ExpertSearchState(
            query=query,
            refined_queries=[],
            normal_vector_results=[],
            normal_keyword_results=[],
            project_vector_results=[],
            project_keyword_results=[],
            merged_results=[],
            final_results=[],
            quality_score=0.0,
            should_refine=False,
            iteration=0
        )

        # Run the graph
        try:
            result = graph.invoke(initial_state)
            experts = result["final_results"]
            
            if not experts:
                print("No experts found. Try rephrasing your query.")
                continue

            print("\nTop Experts (both DBs):")
            for r in experts:
                print(f"• Expert {r['expert_id']} ({r['expert_name']}), score={r['fused_score']:.3f}")
                print("    Headline:   ", r["headline"])
                print("    Bio snippet:", r["bio"][:100], "…")
                print("    Work summary:", r["work_summary"][:100], "…\n")
                
        except Exception as e:
            print(f"Error during search: {e}")


if __name__ == "__main__":
    main()
