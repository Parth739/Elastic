import asyncio
import sys
from workflows.autonomous_workflow import AutonomousExpertSearchWorkflow
from monitoring.background_monitor import BackgroundMonitor
from utils.session_manager import SessionManager
from utils.feedback_manager import FeedbackManager
from models.schemas import Expert, AgentState
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import os
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('expert_search.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AutonomousExpertSearchAgent:
    def __init__(self):
        """Initialize the autonomous expert search agent"""
        print("Initializing Expert Search Agent...")
        try:
            self.workflow = AutonomousExpertSearchWorkflow()
            self.monitor = BackgroundMonitor()
            self.session_manager = SessionManager()
            self.feedback_manager = FeedbackManager()  # Added feedback manager
            self.current_session_id = None
            self.show_reasoning = True
            self.autonomous_mode = False
            self.active_searches = {}
            self.last_strategy_used = None  # Track for feedback
            
            logger.info("Expert Search Agent initialized successfully")
            # print("Agent ready! Fully autonomous capabilities enabled.\n")
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            print(f"Error: {str(e)}")
            raise
    
    async def start_autonomous_mode(self):
        """Start fully autonomous operation"""
        self.autonomous_mode = True
        monitor_task = asyncio.create_task(self.monitor.start_monitoring())
        return monitor_task
    
    def display_reasoning(self, reasoning_traces):
        """Display reasoning traces"""
        if not self.show_reasoning or not reasoning_traces:
            return
        
        print("\nAgent Reasoning Process:")
        print("=" * 70)
        
        for i, trace in enumerate(reasoning_traces, 1):
            confidence = f" (confidence: {trace.confidence:.2f})" if trace.confidence > 0 else ""
            print(f"\n[{i}] {trace.step}{confidence}")
            print("-" * 50)
            print(f"Reasoning: {trace.reasoning}")
            if trace.decision:
                print(f"Decision: {trace.decision}")
    
    def display_experts(self, experts: List[Expert]):
        """Display experts with enhanced information"""
        if not experts:
            print("No experts found yet. Agent will continue searching...")
            return
        
        print(f"\nFound {len(experts)} experts:")
        print("=" * 70)
        
        for i, expert in enumerate(experts[:10], 1):
            print(f"\n[{i}] Expert ID: {expert.id}")
            print(f"    Headline: {expert.headline}")
            print(f"    Location: {expert.base_location or 'Location not specified'}")
            print(f"    Experience: {expert.total_years_of_experience or 'N/A'} years")
            print(f"    Bio: {expert.bio[:100]}...")
            print(f"    Score: {expert.score:.2f}")
            
            if expert.relevance_explanation:
                print(f"    Why relevant: {expert.relevance_explanation}")

    async def collect_feedback(self, query: str, experts: List[Expert], session_id: str):
        """Collect user feedback after showing results"""
        print("\nHow satisfied are you with these results?")
        print("Rate from 1-5 (1=Very Dissatisfied, 5=Very Satisfied)")
        print("Or press Enter to skip feedback")
        
        while True:
            try:
                rating_input = input("Your rating: ").strip()
                
                # Allow skipping
                if not rating_input:
                    print("Feedback skipped.")
                    return
                
                rating = int(rating_input)
                if 1 <= rating <= 5:
                    # Convert to 0-1 scale
                    satisfaction_score = (rating - 1) / 4.0
                    
                    # Ask for optional comments
                    print("\nAny specific feedback? (Press Enter to skip)")
                    comments = input("Comments: ").strip() or None
                    
                    # Store feedback
                    self.feedback_manager.add_search_feedback(
                        session_id=session_id,
                        query=query,
                        experts=experts,
                        satisfaction_score=satisfaction_score,
                        comments=comments
                    )
                    
                    # Update learning based on feedback
                    if self.last_strategy_used:
                        self.workflow.learning_agent.learn_from_search(
                            query=query,
                            strategy=self.last_strategy_used,
                            experts=experts,
                            user_feedback=satisfaction_score
                        )
                    
                    print("Thank you! Your feedback helps improve future searches.")
                    
                    # Show immediate impact
                    if satisfaction_score >= 0.75:
                        print(f"Great! I'll prioritize similar strategies for '{query.split()[0]}...' queries")
                    elif satisfaction_score <= 0.25:
                        print("I'll try different approaches for similar queries next time")
                    
                    break
                else:
                    print("Please enter a number between 1 and 5")
                    
            except ValueError:
                print("Please enter a valid number (1-5) or press Enter to skip")
    
    async def autonomous_search(self, query: str, target_quality: float = 0.8):
        """Perform fully autonomous search with feedback collection"""
        if not self.current_session_id:
            self.current_session_id = self.session_manager.create_session()

        search_id = f"search_{datetime.now().timestamp()}"
        self.active_searches[search_id] = {
            "query": query,
            "status": "active",
            "start_time": datetime.now()
        }

        print(f"\nStarting Autonomous Search")
        print(f"Query: {query}")
        print(f"Target Quality: {target_quality}")
        print(f"Mode: Unlimited persistence with continuous learning")
        print("=" * 70)

        try:
            # Run autonomous workflow
            result = await self.workflow.run(query, target_quality)
            
            # Extract last strategy used from reasoning traces
            for trace in reversed(result.reasoning_traces):
                if trace.step == "Strategy Selection" and trace.decision:
                    self.last_strategy_used = trace.decision
                    break

            # Display reasoning
            if self.show_reasoning:
                self.display_reasoning(result.reasoning_traces)

            # Display results
            self.display_experts(result.experts)

            # Display quality and suggestions
            print(f"\nSearch Quality: {result.quality_score:.2f}")

            if result.suggestions:
                print("\nSuggestions for better results:")
                for suggestion in result.suggestions:
                    print(f"  - {suggestion}")

            if result.alternative_queries:
                print("\nAlternative queries to try:")
                for alt_query in result.alternative_queries:
                    print(f"  - {alt_query}")

            # Add to monitoring if quality is below target
            if result.quality_score < target_quality:
                self.monitor.add_monitored_search(search_id, query, result)
                print(f"\nAdded to background monitoring for continuous improvement")

            # Update session
            self.session_manager.add_to_history(
                self.current_session_id,
                query,
                result.dict()
            )

            self.active_searches[search_id]["status"] = "complete"
            self.active_searches[search_id]["quality"] = result.quality_score
            
            # COLLECT FEEDBACK - This is the key addition!
            if result.experts:
                await self.collect_feedback(
                    query=query,
                    experts=result.experts,
                    session_id=self.current_session_id
                )
            
            return result

        except Exception as e:
            logger.error(f"Autonomous search error: {e}")
            print(f"\nError: {str(e)}")  # Fixed syntax error here
            self.active_searches[search_id]["status"] = "error"

    async def interactive_mode(self):
        """Run in interactive mode with autonomous features"""
        print("\n Expert Search Agent")
        # print("=" * 70)
        # print("I'm your autonomous AI agent that will:")
        # print("  - Learn from every search")
        # print("  - Continuously improve results")
        # print("  - Try multiple strategies automatically")
        # print("  - Monitor for better matches in the background")
        # print("\nJust tell me what experts you need!")
        # print("=" * 70)
        
        # Start background monitoring in interactive mode
        if not self.autonomous_mode:
            monitor_task = await self.start_autonomous_mode()
        
        while True:
            try:
                command = input("\nAgent> ").strip()
                
                if not command:
                    continue
                
                # Handle commands
                if command.lower() in ['exit', 'quit']:
                    print("\nShutting down autonomous agent...")
                    await self.monitor.stop_monitoring()
                    break
                
                elif command.lower() == 'status':
                    self.show_status()
                
                elif command.lower() == 'help':
                    self.show_help()
                
                elif command.lower().startswith('reasoning'):
                    if 'off' in command:
                        self.show_reasoning = False
                        print("Reasoning display OFF")
                    else:
                        self.show_reasoning = True
                        print("Reasoning display ON")
                
                else:
                    # Treat as search query
                    await self.autonomous_search(command)
                    
            except KeyboardInterrupt:
                print("\nInterrupted. Type 'exit' to quit.")
            except Exception as e:
                logger.error(f"Error: {e}")
                print(f"\nError: {str(e)}")  # Fixed syntax error here
    
    def show_status(self):
        """Show agent status"""
        print("\nAgent Status")
        print("=" * 50)
        print(f"Autonomous Mode: {'ON' if self.autonomous_mode else 'OFF'}")
        print(f"Active Searches: {len([s for s in self.active_searches.values() if s['status'] == 'active'])}")
        print(f"Monitored Searches: {len(self.monitor.monitored_searches)}")
        print(f"Learning Records: {len(self.workflow.learning_agent.storage.learning_records)}")
        
        # Show strategies performance
        print("\nStrategy Performance:")
        for name, strategy in self.workflow.learning_agent.storage.strategies.items():
            print(f"  - {name}: {strategy.success_rate:.2f} success rate ({strategy.usage_count} uses)")
    
    def show_help(self):
        """Show help"""
        # print("\nAutonomous Agent Commands:")
        # print("-" * 50)
        # print("  Just type what experts you're looking for!")
        # print("  status         - Show agent status")
        # print("  reasoning off  - Turn off reasoning display")
        # print("  help          - Show this help")
        # print("  exit          - Stop the agent")
        # print("\nThe agent will automatically:")
        # print("  - Try multiple search strategies")
        # print("  - Learn from successes and failures")
        # print("  - Monitor for better matches")
        # print("  - Suggest improvements")

async def main():
    """Main entry point"""
    try:
        agent = AutonomousExpertSearchAgent()
        await agent.interactive_mode()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\nFatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
