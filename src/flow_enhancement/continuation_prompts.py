"""
Dynamic continuation prompts generator for agent flow enhancement.
Analyzes query context and suggests natural follow-up questions to encourage deeper exploration.
"""

import json
import re
from typing import Dict, List, Optional, Any
from enum import Enum

class ExplorationContext(Enum):
    """Types of exploration contexts that require different continuation strategies."""
    INITIAL_OVERVIEW = "initial_overview"
    ARCHITECTURE_ANALYSIS = "architecture_analysis"
    IMPLEMENTATION_DETAILS = "implementation_details"
    PATTERN_RECOGNITION = "pattern_recognition"
    COMPARISON_STUDY = "comparison_study"
    DEEP_DIVE = "deep_dive"

class ContinuationPromptsGenerator:
    """
    Generates contextual follow-up prompts to guide agents into deeper exploration.
    Breaks the one-loop pattern by suggesting natural next questions.
    """
    
    def __init__(self):
        self.context_patterns = self._initialize_context_patterns()
        self.depth_progressions = self._initialize_depth_progressions()
        
    def _initialize_context_patterns(self) -> Dict[ExplorationContext, Dict[str, List[str]]]:
        """Initialize patterns for detecting exploration context from queries."""
        return {
            ExplorationContext.INITIAL_OVERVIEW: {
                "triggers": ["what does", "what is", "overview", "summary", "purpose", "about"],
                "depth_level": 1,
                "natural_progressions": ["architecture", "implementation", "patterns", "components"]
            },
            ExplorationContext.ARCHITECTURE_ANALYSIS: {
                "triggers": ["architecture", "structure", "design", "components", "modules", "system"],
                "depth_level": 2,
                "natural_progressions": ["implementation", "patterns", "decisions", "dependencies"]
            },
            ExplorationContext.IMPLEMENTATION_DETAILS: {
                "triggers": ["how does", "implementation", "algorithm", "logic", "code", "function"],
                "depth_level": 3,
                "natural_progressions": ["patterns", "optimization", "edge cases", "testing"]
            },
            ExplorationContext.PATTERN_RECOGNITION: {
                "triggers": ["pattern", "approach", "method", "strategy", "technique", "best practice"],
                "depth_level": 4,
                "natural_progressions": ["comparison", "alternatives", "trade-offs", "application"]
            }
        }
    
    def _initialize_depth_progressions(self) -> Dict[str, List[str]]:
        """Initialize natural progression paths for different exploration areas."""
        return {
            "authentication": [
                "How does the authentication flow work?",
                "What security patterns are implemented?", 
                "How are tokens/sessions managed?",
                "What are the security trade-offs made here?"
            ],
            "database": [
                "How is data modeling structured?",
                "What query optimization strategies are used?",
                "How is database scaling handled?",
                "What are the performance patterns?"
            ],
            "api": [
                "How is API versioning handled?", 
                "What error handling patterns are used?",
                "How is rate limiting implemented?",
                "What design decisions shaped the API?"
            ],
            "frontend": [
                "How is state management structured?",
                "What component patterns are used?",
                "How is performance optimized?",
                "What are the UX decision patterns?"
            ],
            "microservices": [
                "How do services communicate?",
                "What fault tolerance patterns are used?",
                "How is service discovery handled?",
                "What are the distributed system trade-offs?"
            ],
            "performance": [
                "What caching strategies are implemented?",
                "How is scaling handled?",
                "What optimization techniques are used?",
                "Where are the performance bottlenecks?"
            ]
        }
    
    def detect_exploration_context(self, query: str, previous_queries: Optional[List[str]] = None) -> ExplorationContext:
        """
        Detect the current exploration context based on query content.
        
        Args:
            query: Current query being processed
            previous_queries: List of previous queries in the session
            
        Returns:
            ExplorationContext enum indicating the type of exploration
        """
        query_lower = query.lower()
        
        # Check for context patterns
        for context, config in self.context_patterns.items():
            for trigger in config["triggers"]:
                if trigger in query_lower:
                    return context
        
        # Default to initial overview if no specific context detected
        return ExplorationContext.INITIAL_OVERVIEW
    
    def identify_domain_focus(self, query: str, response_content: str = "") -> List[str]:
        """
        Identify the primary domain areas mentioned in the query/response.
        
        Args:
            query: The query being processed
            response_content: Optional response content to analyze
            
        Returns:
            List of domain areas (e.g., ['authentication', 'database'])
        """
        combined_text = (query + " " + response_content).lower()
        identified_domains = []
        
        domain_keywords = {
            "authentication": ["auth", "login", "security", "token", "session", "user", "password"],
            "database": ["database", "db", "sql", "query", "table", "schema", "data", "persistence"],
            "api": ["api", "endpoint", "rest", "graphql", "request", "response", "http"],
            "frontend": ["frontend", "ui", "component", "react", "vue", "angular", "dom"],
            "microservices": ["service", "microservice", "distributed", "communication", "messaging"],
            "performance": ["performance", "speed", "optimization", "cache", "latency", "throughput"],
            "testing": ["test", "testing", "spec", "unit", "integration", "mock"],
            "deployment": ["deploy", "deployment", "docker", "kubernetes", "infrastructure"]
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                identified_domains.append(domain)
        
        return identified_domains or ["general"]
    
    def generate_continuation_prompts(
        self, 
        query: str, 
        response_content: str = "",
        session_id: Optional[str] = None,
        previous_queries: Optional[List[str]] = None,
        query_count: int = 1
    ) -> Dict[str, Any]:
        """
        Generate contextual continuation prompts to encourage deeper exploration.
        
        Args:
            query: Current query that was just processed
            response_content: The response content (optional for better context)
            session_id: Current session ID
            previous_queries: Previous queries in the session
            query_count: Number of queries in current session
            
        Returns:
            Dictionary containing continuation prompts and session guidance
        """
        context = self.detect_exploration_context(query, previous_queries)
        domains = self.identify_domain_focus(query, response_content)
        
        # Generate natural follow-up questions
        follow_up_questions = self._generate_follow_up_questions(context, domains, query_count)
        
        # Generate curiosity hooks
        curiosity_hooks = self._generate_curiosity_hooks(context, domains)
        
        # Generate depth progression indicators
        depth_info = self._generate_depth_indicators(context, query_count)
        
        # Generate session continuity guidance
        session_guidance = self._generate_session_guidance(session_id, query_count)
        
        return {
            "follow_up_questions": follow_up_questions,
            "curiosity_hooks": curiosity_hooks,
            "depth_info": depth_info,
            "session_guidance": session_guidance,
            "exploration_momentum": self._generate_momentum_builders(context, domains)
        }
    
    def _generate_follow_up_questions(self, context: ExplorationContext, domains: List[str], query_count: int) -> List[str]:
        """Generate 3-4 natural follow-up questions based on context."""
        questions = []
        
        # Domain-specific questions
        for domain in domains[:2]:  # Limit to top 2 domains
            if domain in self.depth_progressions:
                domain_questions = self.depth_progressions[domain]
                # Select questions based on query count to avoid repetition
                start_idx = min(query_count - 1, len(domain_questions) - 2)
                questions.extend(domain_questions[start_idx:start_idx + 2])
        
        # Context-specific questions
        if context == ExplorationContext.INITIAL_OVERVIEW:
            questions.extend([
                "What are the key architectural decisions made here?",
                "How do the main components interact?",
                "What patterns and conventions are followed?"
            ])
        elif context == ExplorationContext.ARCHITECTURE_ANALYSIS:
            questions.extend([
                "What design trade-offs were made and why?",
                "How does this compare to alternative approaches?",
                "What are the scalability implications?"
            ])
        elif context == ExplorationContext.IMPLEMENTATION_DETAILS:
            questions.extend([
                "What edge cases does this handle?",
                "How is error handling implemented?",
                "What optimization techniques are used?"
            ])
        
        # Return top 4 unique questions
        unique_questions = list(dict.fromkeys(questions))  # Remove duplicates while preserving order
        return unique_questions[:4]
    
    def _generate_curiosity_hooks(self, context: ExplorationContext, domains: List[str]) -> List[str]:
        """Generate curiosity-inducing transition phrases."""
        hooks = [
            "But wait, there's an interesting pattern here...",
            "This reveals something deeper about the architecture...",
            "Here's where it gets interesting...",
            "The real insight comes when you look at...",
            "This connects to a broader pattern you might find valuable..."
        ]
        
        # Context-specific hooks
        if context == ExplorationContext.INITIAL_OVERVIEW:
            hooks.extend([
                "Now that you see the big picture, the implementation details will make much more sense...",
                "The architectural choices here suggest some interesting design philosophy..."
            ])
        
        return hooks[:3]  # Return top 3 hooks
    
    def _generate_depth_indicators(self, context: ExplorationContext, query_count: int) -> Dict[str, Any]:
        """Generate exploration depth indicators."""
        depth_levels = {
            1: {"level": "Surface", "description": "Basic understanding", "next": "Dive into implementation"},
            2: {"level": "Implementation", "description": "Understanding how it works", "next": "Explore architectural patterns"}, 
            3: {"level": "Architecture", "description": "Understanding design decisions", "next": "Analyze patterns and trade-offs"},
            4: {"level": "Patterns", "description": "Understanding reusable insights", "next": "Compare with other approaches"},
            5: {"level": "Mastery", "description": "Deep understanding ready for application", "next": "Synthesize learnings"}
        }
        
        current_depth = min(query_count, 5)
        current_info = depth_levels[current_depth]
        
        return {
            "current_depth": current_depth,
            "level_name": current_info["level"],
            "description": current_info["description"],
            "next_level": current_info["next"],
            "completion_percentage": min((current_depth / 5) * 100, 100)
        }
    
    def _generate_session_guidance(self, session_id: Optional[str], query_count: int) -> Dict[str, Any]:
        """Generate session persistence and continuity guidance."""
        if not session_id:
            return {
                "message": "💡 Consider using a session_id to build compound understanding across multiple queries",
                "benefit": "Session continuity allows deeper exploration and pattern recognition"
            }
        
        return {
            "session_id": session_id,
            "query_count": query_count,
            "message": f"🔄 Session {session_id[:8]}... | Query #{query_count} | Building compound understanding",
            "continuity_tip": "Keep using this session_id to build deeper insights and connect patterns",
            "exploration_status": self._get_exploration_status(query_count)
        }
    
    def _generate_momentum_builders(self, context: ExplorationContext, domains: List[str]) -> List[str]:
        """Generate momentum-building phrases that prevent stopping."""
        builders = [
            "Ready to go deeper?",
            "This opens up some interesting follow-up questions...",
            "Now that you understand this part, let's explore how it connects...",
            "The next layer reveals even more insights...",
            "Building on this understanding, you might want to explore..."
        ]
        
        return builders[:2]
    
    def _get_exploration_status(self, query_count: int) -> str:
        """Get exploration status message based on query count."""
        if query_count == 1:
            return "Just getting started - the real insights come with deeper exploration"
        elif query_count < 3:
            return "Building initial understanding - ready for deeper patterns"
        elif query_count < 5:
            return "Developing architectural insight - patterns emerging"
        else:
            return "Deep exploration mode - perfect for pattern synthesis and learning extraction"
    
    def format_for_response(self, prompts_data: Dict[str, Any]) -> str:
        """
        Format continuation prompts for embedding in tool responses.
        
        Args:
            prompts_data: Output from generate_continuation_prompts()
            
        Returns:
            Formatted string for embedding in response
        """
        formatted = "\n\n" + "="*50 + "\n"
        formatted += "🚀 **Exploration Pathways** | Continue Building Understanding\n"
        formatted += "="*50 + "\n"
        
        # Session info
        session_info = prompts_data["session_guidance"]
        if "session_id" in session_info:
            formatted += f"📊 {session_info['message']}\n"
            formatted += f"💡 {session_info['continuity_tip']}\n"
        else:
            formatted += f"💡 {session_info['message']}\n"
        
        formatted += f"🎯 Status: {session_info.get('exploration_status', 'Exploring...')}\n\n"
        
        # Depth indicator
        depth = prompts_data["depth_info"]
        formatted += f"📈 **Exploration Depth**: {depth['level_name']} ({depth['completion_percentage']:.0f}%)\n"
        formatted += f"   Current: {depth['description']}\n"
        formatted += f"   Next: {depth['next_level']}\n\n"
        
        # Follow-up questions
        questions = prompts_data["follow_up_questions"]
        if questions:
            formatted += "❓ **Natural Next Questions**:\n"
            for i, question in enumerate(questions, 1):
                formatted += f"   {i}. {question}\n"
            formatted += "\n"
        
        # Curiosity hook
        hooks = prompts_data["curiosity_hooks"]
        if hooks:
            formatted += f"🔍 {hooks[0]}\n\n"
        
        # Momentum builders
        momentum = prompts_data["exploration_momentum"]
        if momentum:
            formatted += f"⚡ {momentum[0]}\n"
        
        formatted += "="*50
        
        return formatted