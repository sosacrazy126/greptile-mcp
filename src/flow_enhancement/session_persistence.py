"""
Session persistence manager for maintaining compound learning across agent interactions.
Provides guidance and tracking for session continuity to break the one-loop pattern.
"""

import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class SessionMetadata:
    """Metadata for tracking session exploration progress."""
    session_id: str
    created_at: float
    last_active: float
    query_count: int
    exploration_domains: List[str]
    depth_achieved: int
    patterns_discovered: List[str]
    connections_made: List[str]

class SessionPersistenceManager:
    """
    Manages session persistence and provides guidance for compound learning.
    Tracks exploration progress and suggests cross-session connections.
    """
    
    def __init__(self):
        self.sessions: Dict[str, SessionMetadata] = {}
        self.domain_patterns: Dict[str, List[str]] = {}
        self.cross_session_connections: Dict[str, List[str]] = {}
        
    def track_session_query(
        self,
        session_id: str,
        query: str,
        domains: List[str],
        response_content: str = ""
    ) -> SessionMetadata:
        """
        Track a new query in a session and update metadata.
        
        Args:
            session_id: Session identifier
            query: Query that was executed
            domains: Domains identified in the query
            response_content: Response content for pattern analysis
            
        Returns:
            Updated session metadata
        """
        current_time = time.time()
        
        if session_id not in self.sessions:
            # Create new session
            self.sessions[session_id] = SessionMetadata(
                session_id=session_id,
                created_at=current_time,
                last_active=current_time,
                query_count=1,
                exploration_domains=domains,
                depth_achieved=1,
                patterns_discovered=[],
                connections_made=[]
            )
        else:
            # Update existing session
            session = self.sessions[session_id]
            session.last_active = current_time
            session.query_count += 1
            session.depth_achieved = min(session.query_count, 5)  # Max depth of 5
            
            # Add new domains
            for domain in domains:
                if domain not in session.exploration_domains:
                    session.exploration_domains.append(domain)
        
        # Analyze patterns and connections
        self._analyze_patterns(session_id, query, response_content)
        self._identify_cross_session_connections(session_id, domains)
        
        return self.sessions[session_id]
    
    def get_session_guidance(self, session_id: str) -> Dict[str, Any]:
        """
        Get session persistence guidance for agents.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with session guidance and recommendations
        """
        if session_id not in self.sessions:
            return {
                "status": "new_session",
                "message": "Starting new exploration session - maintain this session_id for compound learning",
                "benefits": [
                    "Build deeper understanding over multiple queries",
                    "Connect patterns across different explorations", 
                    "Develop architectural insights through progressive exploration",
                    "Create personal knowledge accumulation"
                ],
                "recommendation": f"Keep using session_id='{session_id}' for all related queries"
            }
        
        session = self.sessions[session_id]
        session_age = time.time() - session.created_at
        
        guidance = {
            "status": "continuing_session",
            "session_id": session_id,
            "query_count": session.query_count,
            "exploration_duration": self._format_duration(session_age),
            "domains_explored": session.exploration_domains,
            "depth_achieved": session.depth_achieved,
            "message": self._generate_continuity_message(session),
            "momentum_status": self._get_momentum_status(session),
            "compound_learning_benefits": self._get_compound_benefits(session)
        }
        
        # Add cross-session connections if available
        if session_id in self.cross_session_connections:
            guidance["connections"] = {
                "related_sessions": self.cross_session_connections[session_id],
                "message": "This exploration connects to patterns from previous sessions"
            }
        
        return guidance
    
    def suggest_session_continuation(self, session_id: str, last_query: str) -> List[str]:
        """
        Suggest ways to continue the session exploration.
        
        Args:
            session_id: Session identifier
            last_query: The last query executed
            
        Returns:
            List of continuation suggestions
        """
        if session_id not in self.sessions:
            return []
        
        session = self.sessions[session_id]
        suggestions = []
        
        # Based on depth achieved
        if session.depth_achieved <= 2:
            suggestions.extend([
                "Explore the architectural patterns used in this codebase",
                "Dive deeper into the implementation details",
                "Understand the design decisions and trade-offs made"
            ])
        elif session.depth_achieved <= 4:
            suggestions.extend([
                "Compare these patterns with other codebases you've explored", 
                "Analyze the performance implications of these design choices",
                "Explore edge cases and error handling strategies"
            ])
        else:
            suggestions.extend([
                "Synthesize the key learnings from this exploration",
                "Identify reusable patterns for your own projects",
                "Connect insights with patterns from other domains"
            ])
        
        # Based on domains explored
        unexplored_domains = self._suggest_unexplored_domains(session.exploration_domains)
        if unexplored_domains:
            suggestions.extend([
                f"Explore the {domain} aspects of this codebase" for domain in unexplored_domains[:2]
            ])
        
        return suggestions[:4]  # Return top 4 suggestions
    
    def get_cross_session_insights(self, current_session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get insights from cross-session pattern analysis.
        
        Args:
            current_session_id: Current session identifier
            
        Returns:
            Cross-session insights if available
        """
        if current_session_id not in self.sessions:
            return None
        
        current_session = self.sessions[current_session_id]
        related_sessions = []
        
        # Find sessions with overlapping domains
        for session_id, session in self.sessions.items():
            if session_id == current_session_id:
                continue
                
            overlap = set(current_session.exploration_domains) & set(session.exploration_domains)
            if overlap:
                related_sessions.append({
                    "session_id": session_id,
                    "overlapping_domains": list(overlap),
                    "patterns_discovered": session.patterns_discovered,
                    "exploration_depth": session.depth_achieved
                })
        
        if not related_sessions:
            return None
        
        return {
            "related_sessions": related_sessions[:3],  # Top 3 related sessions
            "synthesis_opportunity": "You can now compare patterns across multiple codebases",
            "compound_insights": self._generate_compound_insights(current_session, related_sessions)
        }
    
    def _analyze_patterns(self, session_id: str, query: str, response_content: str):
        """Analyze and store patterns discovered in the session."""
        session = self.sessions[session_id]
        
        # Simple pattern detection based on keywords
        pattern_keywords = {
            "singleton": ["singleton", "single instance", "global state"],
            "factory": ["factory", "create", "builder"],
            "observer": ["observer", "listener", "event", "subscribe"],
            "mvc": ["model", "view", "controller", "mvc"],
            "microservices": ["service", "distributed", "api gateway"],
            "caching": ["cache", "redis", "memcache", "storage"],
            "authentication": ["auth", "token", "jwt", "session"],
            "error_handling": ["error", "exception", "try", "catch"]
        }
        
        combined_text = (query + " " + response_content).lower()
        
        for pattern, keywords in pattern_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                if pattern not in session.patterns_discovered:
                    session.patterns_discovered.append(pattern)
    
    def _identify_cross_session_connections(self, session_id: str, domains: List[str]):
        """Identify connections with other sessions exploring similar domains."""
        for existing_session_id, session in self.sessions.items():
            if existing_session_id == session_id:
                continue
            
            # Check for domain overlap
            overlap = set(domains) & set(session.exploration_domains)
            if overlap:
                if session_id not in self.cross_session_connections:
                    self.cross_session_connections[session_id] = []
                
                if existing_session_id not in self.cross_session_connections[session_id]:
                    self.cross_session_connections[session_id].append(existing_session_id)
    
    def _generate_continuity_message(self, session: SessionMetadata) -> str:
        """Generate a message encouraging session continuity."""
        if session.query_count == 1:
            return "Session started! Each additional query builds deeper understanding."
        elif session.query_count < 3:
            return f"Building momentum (Query #{session.query_count}) - real insights emerge with continued exploration."
        elif session.query_count < 5:
            return f"Deep exploration mode (Query #{session.query_count}) - you're uncovering architectural patterns!"
        else:
            return f"Expert-level exploration (Query #{session.query_count}) - perfect for pattern synthesis and knowledge extraction."
    
    def _get_momentum_status(self, session: SessionMetadata) -> Dict[str, Any]:
        """Get momentum status for the session."""
        time_since_creation = time.time() - session.created_at
        time_since_last = time.time() - session.last_active
        
        if time_since_last > 3600:  # 1 hour
            momentum = "cooling"
            message = "Session has been idle - perfect time to continue exploration"
        elif session.query_count >= 3:
            momentum = "high"
            message = "Strong exploration momentum - insights are compounding!"
        elif session.query_count >= 2:
            momentum = "building"
            message = "Momentum building - patterns starting to emerge"
        else:
            momentum = "starting"
            message = "Just getting started - the next few queries unlock deeper insights"
        
        return {
            "level": momentum,
            "message": message,
            "queries_to_insight": max(3 - session.query_count, 0)
        }
    
    def _get_compound_benefits(self, session: SessionMetadata) -> List[str]:
        """Get compound learning benefits achieved in this session."""
        benefits = []
        
        if session.query_count >= 2:
            benefits.append("Building contextual understanding across multiple queries")
        
        if session.query_count >= 3:
            benefits.append("Discovering architectural patterns and design decisions")
        
        if session.query_count >= 4:
            benefits.append("Developing deep insights for practical application")
        
        if len(session.exploration_domains) > 1:
            benefits.append(f"Connecting patterns across {len(session.exploration_domains)} domains")
        
        if session.patterns_discovered:
            benefits.append(f"Identified {len(session.patterns_discovered)} reusable patterns")
        
        return benefits
    
    def _suggest_unexplored_domains(self, explored_domains: List[str]) -> List[str]:
        """Suggest domains that haven't been explored yet."""
        all_domains = ["authentication", "database", "api", "frontend", "performance", "testing", "deployment", "security"]
        return [domain for domain in all_domains if domain not in explored_domains]
    
    def _generate_compound_insights(self, current_session: SessionMetadata, related_sessions: List[Dict]) -> List[str]:
        """Generate compound insights from cross-session analysis."""
        insights = []
        
        if len(related_sessions) >= 2:
            insights.append("You now have data points from multiple codebases for pattern comparison")
        
        common_domains = set(current_session.exploration_domains)
        for session in related_sessions:
            common_domains &= set(session["overlapping_domains"])
        
        if common_domains:
            insights.append(f"Common patterns in {list(common_domains)[0]} domain across multiple codebases")
        
        total_patterns = len(current_session.patterns_discovered)
        for session in related_sessions:
            total_patterns += len(session["patterns_discovered"])
        
        if total_patterns >= 5:
            insights.append(f"Rich pattern library ({total_patterns} patterns) emerging from cross-codebase exploration")
        
        return insights
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds/60)}m"
        else:
            hours = int(seconds/3600)
            minutes = int((seconds % 3600)/60)
            return f"{hours}h {minutes}m"
    
    def format_persistence_guidance(self, session_id: str) -> str:
        """
        Format session persistence guidance for embedding in responses.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Formatted guidance string
        """
        guidance = self.get_session_guidance(session_id)
        
        if guidance["status"] == "new_session":
            formatted = f"""
🔄 **Session Persistence Guide**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 **New Exploration Session Started**
   Session ID: {session_id[:12]}...
   
🎯 **Keep This Session Active**: Use the same session_id for all related queries
   Benefits: {', '.join(guidance['benefits'][:2])}

🚀 **Compound Learning**: Each query builds on previous understanding
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        else:
            formatted = f"""
🔄 **Session Continuity Active**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Session: {session_id[:12]}... | Query #{guidance['query_count']} | {guidance['exploration_duration']}
🎯 Domains: {', '.join(guidance['domains_explored'][:3])}
⚡ Momentum: {guidance['momentum_status']['message']}

💡 {guidance['message']}
"""
            
            if guidance.get('compound_learning_benefits'):
                formatted += f"\n🌟 Compound Benefits:\n"
                for benefit in guidance['compound_learning_benefits'][:2]:
                    formatted += f"   • {benefit}\n"
            
            formatted += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        return formatted