"""
Cross-Repository Synthesis and Pattern Analysis

Implements specialized synthesis agents for complex multi-repository analysis
following the Claude Code orchestration pattern.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from ..utils import GreptileClient, generate_session_id
from ..logging_config import logger


@dataclass
class PatternAnalysisResult:
    """Result from pattern analysis across repositories."""
    repository: Dict[str, str]
    patterns_found: List[Dict[str, Any]]
    implementation_details: str
    unique_aspects: List[str]
    commonalities: List[str]
    session_id: str
    analysis_time: float


@dataclass
class ExplorationNode:
    """Node in recursive exploration tree."""
    concept: str
    depth: int
    parent: Optional[str]
    children: List[str]
    content: str
    sources: List[Dict[str, Any]]
    exploration_time: float


class CrossRepositorySynthesizer:
    """
    Synthesizes insights across multiple repositories using orchestrated sub-agents.
    
    Implements Claude Code pattern for cross-repository analysis:
    - Lead agent coordinates overall comparison
    - Sub-agents analyze each repository independently  
    - Synthesis agent combines insights and identifies patterns
    """
    
    def __init__(self, client: GreptileClient):
        self.client = client
    
    async def compare_patterns(
        self,
        pattern_focus: str,
        repositories: List[Dict[str, str]],
        session_id: Optional[str] = None,
        depth: str = "architectural"
    ) -> Dict[str, Any]:
        """
        Compare patterns across multiple repositories using orchestrated analysis.
        """
        
        if session_id is None:
            session_id = generate_session_id()
        
        logger.info(
            f"Starting cross-repository pattern comparison: {pattern_focus}",
            session_id=session_id,
            repositories_count=len(repositories)
        )
        
        comparison_start = time.time()
        
        # Phase 1: Individual repository analysis (parallel sub-agents)
        analysis_tasks = []
        for repo in repositories:
            task = self._analyze_repository_pattern(
                pattern_focus=pattern_focus,
                repository=repo,
                session_id=session_id,
                depth=depth
            )
            analysis_tasks.append(task)
        
        # Execute repository analyses in parallel (Claude Code sub-agent pattern)
        repository_analyses = await asyncio.gather(*analysis_tasks, return_exceptions=True)
        
        # Filter successful analyses
        successful_analyses = []
        for i, result in enumerate(repository_analyses):
            if isinstance(result, Exception):
                logger.warning(
                    f"Repository analysis failed: {repositories[i]}",
                    session_id=session_id,
                    error=str(result)
                )
            else:
                successful_analyses.append(result)
        
        if not successful_analyses:
            return {
                "error": "All repository analyses failed",
                "session_id": session_id,
                "repositories_attempted": len(repositories)
            }
        
        # Phase 2: Cross-repository synthesis (specialized synthesis agent)
        synthesis_result = await self._synthesize_cross_repository_insights(
            analyses=successful_analyses,
            pattern_focus=pattern_focus,
            session_id=session_id
        )
        
        comparison_duration = time.time() - comparison_start
        
        return {
            "comparison_result": synthesis_result,
            "repository_analyses": [
                {
                    "repository": analysis.repository,
                    "patterns_found": len(analysis.patterns_found),
                    "unique_aspects": analysis.unique_aspects,
                    "analysis_time": analysis.analysis_time
                }
                for analysis in successful_analyses
            ],
            "session_id": session_id,
            "comparison_metadata": {
                "pattern_focus": pattern_focus,
                "repositories_analyzed": len(successful_analyses),
                "total_repositories": len(repositories),
                "comparison_duration": comparison_duration,
                "depth": depth
            }
        }
    
    async def _analyze_repository_pattern(
        self,
        pattern_focus: str,
        repository: Dict[str, str],
        session_id: str,
        depth: str
    ) -> PatternAnalysisResult:
        """Analyze pattern implementation in a single repository (sub-agent)."""
        
        analysis_start = time.time()
        
        # Customize query based on depth
        if depth == "basic":
            query = f"How is {pattern_focus} implemented in this codebase? Provide a basic overview."
        elif depth == "implementation":
            query = f"Analyze the {pattern_focus} implementation details, including code patterns, design decisions, and specific implementation approaches."
        else:  # architectural
            query = f"Analyze the architectural approach to {pattern_focus} in this codebase, including design patterns, structure, and key architectural decisions."
        
        try:
            # Use query_repository for detailed analysis
            result = await self.client.query_repositories(
                messages=[{"role": "user", "content": query}],
                repositories=[repository],
                session_id=session_id,
                genius=True
            )
            
            analysis_time = time.time() - analysis_start
            
            # Extract patterns and insights (simplified - could be enhanced with NLP)
            content = result.get("message", "")
            sources = result.get("sources", [])
            
            patterns_found = self._extract_patterns(content)
            unique_aspects = self._extract_unique_aspects(content)
            
            return PatternAnalysisResult(
                repository=repository,
                patterns_found=patterns_found,
                implementation_details=content,
                unique_aspects=unique_aspects,
                commonalities=[],  # Will be filled during synthesis
                session_id=session_id,
                analysis_time=analysis_time
            )
            
        except Exception as e:
            logger.error(
                f"Repository pattern analysis failed: {repository}",
                session_id=session_id,
                error=str(e)
            )
            raise
    
    async def _synthesize_cross_repository_insights(
        self,
        analyses: List[PatternAnalysisResult],
        pattern_focus: str,
        session_id: str
    ) -> str:
        """Synthesize insights across repository analyses (synthesis agent)."""
        
        # Build synthesis query incorporating all analyses
        synthesis_query = f"""Based on the analysis of {pattern_focus} across {len(analyses)} repositories, provide a comprehensive comparison that includes:

1. **Common Patterns**: What patterns are shared across repositories?
2. **Unique Approaches**: What unique implementation approaches does each repository take?
3. **Trade-offs**: What are the trade-offs between different approaches?
4. **Best Practices**: What best practices emerge from the comparison?
5. **Recommendations**: What recommendations for implementation or improvement?

Repository Analysis Summaries:
"""
        
        for i, analysis in enumerate(analyses, 1):
            repo_name = f"{analysis.repository.get('remote', 'unknown')}/{analysis.repository.get('repository', 'unknown')}"
            synthesis_query += f"\n{i}. **{repo_name}**:\n{analysis.implementation_details[:500]}...\n"
        
        try:
            # Use query_repository for synthesis
            result = await self.client.query_repositories(
                messages=[{"role": "user", "content": synthesis_query}],
                repositories=[analysis.repository for analysis in analyses],
                session_id=session_id,
                genius=True
            )
            
            return result.get("message", "Synthesis failed")
            
        except Exception as e:
            logger.error(f"Cross-repository synthesis failed", session_id=session_id, error=str(e))
            return f"Synthesis failed: {str(e)}"
    
    def _extract_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Extract patterns from analysis content (simplified implementation)."""
        patterns = []
        
        # Simple pattern extraction based on keywords
        pattern_keywords = [
            "pattern", "architecture", "design", "approach", "strategy",
            "implementation", "structure", "framework", "methodology"
        ]
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in pattern_keywords):
                if len(line) > 20 and len(line) < 200:  # Reasonable length
                    patterns.append({
                        "description": line,
                        "type": "extracted_pattern",
                        "confidence": 0.7  # Simple confidence score
                    })
        
        return patterns[:10]  # Limit to top 10 patterns
    
    def _extract_unique_aspects(self, content: str) -> List[str]:
        """Extract unique aspects from analysis content."""
        unique_aspects = []
        
        # Look for unique, specific, or distinctive mentions
        unique_keywords = [
            "unique", "specific", "distinctive", "particular", "special",
            "novel", "innovative", "custom", "proprietary"
        ]
        
        sentences = content.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence.lower() for keyword in unique_keywords):
                if len(sentence) > 30 and len(sentence) < 150:
                    unique_aspects.append(sentence)
        
        return unique_aspects[:5]  # Limit to top 5 unique aspects


class PatternAnalyzer:
    """
    Recursive pattern analyzer for autonomous codebase exploration.
    
    Implements recursive sub-agent pattern for deep exploration:
    - Each exploration spawns sub-agents for discovered concepts
    - Depth-limited recursion prevents infinite exploration
    - Builds comprehensive exploration tree
    """
    
    def __init__(self, client: GreptileClient):
        self.client = client
        self.exploration_tree: Dict[str, ExplorationNode] = {}
    
    async def explore_recursive(
        self,
        starting_point: str,
        repositories: List[Dict[str, str]],
        session_id: Optional[str] = None,
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """
        Recursively explore codebase starting from a concept or pattern.
        """
        
        if session_id is None:
            session_id = generate_session_id()
        
        logger.info(
            f"Starting recursive exploration: {starting_point}",
            session_id=session_id,
            max_depth=max_depth
        )
        
        exploration_start = time.time()
        
        # Initialize exploration tree
        self.exploration_tree = {}
        
        # Start recursive exploration
        root_node = await self._explore_node(
            concept=starting_point,
            repositories=repositories,
            session_id=session_id,
            depth=0,
            max_depth=max_depth,
            parent=None
        )
        
        exploration_duration = time.time() - exploration_start
        
        # Build exploration summary
        summary = self._build_exploration_summary(root_node, exploration_duration)
        
        return {
            "exploration_summary": summary,
            "exploration_tree": self._serialize_exploration_tree(),
            "session_id": session_id,
            "exploration_metadata": {
                "starting_point": starting_point,
                "max_depth_reached": self._max_depth_reached(),
                "total_nodes": len(self.exploration_tree),
                "exploration_duration": exploration_duration
            }
        }
    
    async def _explore_node(
        self,
        concept: str,
        repositories: List[Dict[str, str]],
        session_id: str,
        depth: int,
        max_depth: int,
        parent: Optional[str]
    ) -> ExplorationNode:
        """Explore a single concept node and recursively explore discovered concepts."""
        
        if depth >= max_depth:
            logger.info(f"Max depth reached for concept: {concept}", session_id=session_id)
            return ExplorationNode(
                concept=concept,
                depth=depth,
                parent=parent,
                children=[],
                content="Max depth reached",
                sources=[],
                exploration_time=0.0
            )
        
        exploration_start = time.time()
        
        # Query for this concept
        query = f"Explore and explain {concept} in this codebase. What related concepts, patterns, or components are connected to this?"
        
        try:
            result = await self.client.query_repositories(
                messages=[{"role": "user", "content": query}],
                repositories=repositories,
                session_id=session_id,
                genius=True
            )
            
            content = result.get("message", "")
            sources = result.get("sources", [])
            
            # Extract related concepts for recursive exploration
            related_concepts = self._extract_related_concepts(content, concept)
            
            exploration_time = time.time() - exploration_start
            
            # Create node
            node = ExplorationNode(
                concept=concept,
                depth=depth,
                parent=parent,
                children=related_concepts,
                content=content,
                sources=sources,
                exploration_time=exploration_time
            )
            
            # Add to exploration tree
            self.exploration_tree[concept] = node
            
            # Recursively explore children (limit to prevent explosion)
            max_children = max(1, 4 - depth)  # Fewer children at deeper levels
            for child_concept in related_concepts[:max_children]:
                if child_concept not in self.exploration_tree:  # Avoid cycles
                    await self._explore_node(
                        concept=child_concept,
                        repositories=repositories,
                        session_id=session_id,
                        depth=depth + 1,
                        max_depth=max_depth,
                        parent=concept
                    )
            
            return node
            
        except Exception as e:
            logger.error(f"Node exploration failed: {concept}", session_id=session_id, error=str(e))
            return ExplorationNode(
                concept=concept,
                depth=depth,
                parent=parent,
                children=[],
                content=f"Exploration failed: {str(e)}",
                sources=[],
                exploration_time=time.time() - exploration_start
            )
    
    def _extract_related_concepts(self, content: str, current_concept: str) -> List[str]:
        """Extract related concepts from exploration content."""
        concepts = []
        
        # Simple concept extraction - look for capitalized terms, technical terms
        import re
        
        # Look for patterns like "ComponentName", "SomePattern", technical terms
        concept_patterns = [
            r'\b[A-Z][a-zA-Z]*(?:[A-Z][a-zA-Z]*)+\b',  # CamelCase
            r'\b[a-z]+[-_][a-z]+\b',  # kebab-case, snake_case
            r'\b(?:pattern|system|component|module|service|handler|manager|controller)\w*\b'  # Technical terms
        ]
        
        for pattern in concept_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if match.lower() != current_concept.lower() and len(match) > 3:
                    concepts.append(match)
        
        # Remove duplicates and return top concepts
        unique_concepts = list(dict.fromkeys(concepts))  # Preserve order while removing duplicates
        return unique_concepts[:5]  # Limit to top 5 related concepts
    
    def _build_exploration_summary(self, root_node: ExplorationNode, duration: float) -> str:
        """Build summary of exploration results."""
        
        summary = f"# Autonomous Exploration: {root_node.concept}\n\n"
        summary += f"Exploration completed in {duration:.2f} seconds\n"
        summary += f"Total concepts explored: {len(self.exploration_tree)}\n\n"
        
        # Build hierarchical summary
        summary += "## Exploration Tree\n\n"
        summary += self._build_tree_summary(root_node.concept, 0)
        
        return summary
    
    def _build_tree_summary(self, concept: str, indent_level: int) -> str:
        """Build hierarchical tree summary."""
        
        if concept not in self.exploration_tree:
            return ""
        
        node = self.exploration_tree[concept]
        indent = "  " * indent_level
        
        summary = f"{indent}- **{concept}** (depth {node.depth})\n"
        summary += f"{indent}  {node.content[:100]}...\n\n"
        
        # Recursively add children
        for child in node.children:
            if child in self.exploration_tree:  # Only include successfully explored children
                summary += self._build_tree_summary(child, indent_level + 1)
        
        return summary
    
    def _max_depth_reached(self) -> int:
        """Get maximum depth reached in exploration."""
        if not self.exploration_tree:
            return 0
        return max(node.depth for node in self.exploration_tree.values())
    
    def _serialize_exploration_tree(self) -> Dict[str, Any]:
        """Serialize exploration tree for JSON output."""
        
        serialized = {}
        for concept, node in self.exploration_tree.items():
            serialized[concept] = {
                "depth": node.depth,
                "parent": node.parent,
                "children": node.children,
                "content_length": len(node.content),
                "sources_count": len(node.sources),
                "exploration_time": node.exploration_time
            }
        
        return serialized