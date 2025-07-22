"""
Multi-Stage Analysis Pipeline Coordinator

Implements the orchestrator-worker pattern for coordinating multiple analysis stages
using session continuity and specialized sub-agents.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# Import existing tools for orchestration
from ..utils import GreptileClient, generate_session_id, normalize_session_id
from ..logging_config import logger


class AnalysisStage(Enum):
    """Analysis pipeline stages following Claude Code sub-agent pattern."""
    DISCOVERY = "discovery"        # Find relevant files and patterns
    ANALYSIS = "analysis"         # Deep architectural understanding
    SYNTHESIS = "synthesis"       # Cross-repository or multi-aspect synthesis
    IMPLEMENTATION = "implementation"  # Specific implementation guidance


@dataclass
class StageResult:
    """Result from a single analysis stage."""
    stage: AnalysisStage
    success: bool
    content: str
    sources: List[Dict[str, Any]]
    session_id: str
    execution_time: float
    metadata: Dict[str, Any]


@dataclass
class PipelineConfig:
    """Configuration for analysis pipeline execution."""
    max_parallel_stages: int = 3
    stage_timeout: float = 120.0
    enable_cross_stage_synthesis: bool = True
    session_persistence: bool = True
    include_implementation_examples: bool = False


class MultiStageCoordinator:
    """
    Coordinates multi-stage analysis pipeline using Claude Code orchestration patterns.
    
    Implements:
    - Lead agent analysis and task decomposition
    - Specialized sub-agent spawning for each stage
    - Parallel execution where beneficial
    - Result synthesis and integration
    """
    
    def __init__(self, client: GreptileClient, config: PipelineConfig = None):
        self.client = client
        self.config = config or PipelineConfig()
        self._stage_results: Dict[str, List[StageResult]] = {}
    
    async def execute_pipeline(
        self,
        query: str,
        repositories: List[Dict[str, str]],
        session_id: Optional[str] = None,
        stages: List[AnalysisStage] = None
    ) -> Dict[str, Any]:
        """
        Execute multi-stage analysis pipeline with orchestrated sub-agents.
        
        Following Claude Code pattern:
        1. Lead agent analyzes task and decomposes into stages
        2. Spawn specialized sub-agents for each stage
        3. Execute stages (parallel where possible)
        4. Synthesize results into unified output
        """
        
        # Initialize session
        if session_id is None:
            session_id = generate_session_id()
        
        # Default stages if not specified
        if stages is None:
            stages = [AnalysisStage.DISCOVERY, AnalysisStage.ANALYSIS, AnalysisStage.IMPLEMENTATION]
        
        logger.info(
            f"Starting multi-stage pipeline: {len(stages)} stages",
            session_id=session_id,
            stages=[s.value for s in stages]
        )
        
        pipeline_start = time.time()
        stage_results = []
        
        # Execute stages sequentially (with session continuity) or parallel (where independent)
        for i, stage in enumerate(stages):
            try:
                # Determine if stage can run in parallel with previous
                can_parallel = self._can_run_parallel(stage, stages[:i])
                
                if can_parallel and i > 0:
                    # Execute in parallel with previous stage
                    logger.info(f"Executing stage {stage.value} in parallel", session_id=session_id)
                    # For now, implement sequentially - parallel execution needs careful session management
                
                # Execute stage with specialized sub-agent
                result = await self._execute_stage(
                    stage=stage,
                    query=query,
                    repositories=repositories,
                    session_id=session_id,
                    previous_results=stage_results
                )
                
                stage_results.append(result)
                
                if not result.success:
                    logger.warning(f"Stage {stage.value} failed, continuing pipeline", session_id=session_id)
                
            except Exception as e:
                logger.error(f"Stage {stage.value} error: {str(e)}", session_id=session_id)
                # Continue pipeline with failed stage marked
                stage_results.append(StageResult(
                    stage=stage,
                    success=False,
                    content=f"Stage failed: {str(e)}",
                    sources=[],
                    session_id=session_id,
                    execution_time=0.0,
                    metadata={"error": str(e)}
                ))
        
        # Synthesize results
        synthesis_result = await self._synthesize_results(
            stage_results=stage_results,
            original_query=query,
            session_id=session_id
        )
        
        pipeline_duration = time.time() - pipeline_start
        
        # Build comprehensive response
        return {
            "pipeline_result": synthesis_result,
            "stage_results": [
                {
                    "stage": r.stage.value,
                    "success": r.success,
                    "content": r.content,
                    "sources": r.sources,
                    "execution_time": r.execution_time,
                    "metadata": r.metadata
                }
                for r in stage_results
            ],
            "session_id": session_id,
            "pipeline_metadata": {
                "total_stages": len(stages),
                "successful_stages": sum(1 for r in stage_results if r.success),
                "total_duration": pipeline_duration,
                "stages_executed": [s.value for s in stages],
                "config": {
                    "max_parallel_stages": self.config.max_parallel_stages,
                    "cross_stage_synthesis": self.config.enable_cross_stage_synthesis
                }
            }
        }
    
    async def _execute_stage(
        self,
        stage: AnalysisStage,
        query: str,
        repositories: List[Dict[str, str]],
        session_id: str,
        previous_results: List[StageResult]
    ) -> StageResult:
        """Execute a single analysis stage with specialized sub-agent approach."""
        
        stage_start = time.time()
        
        # Customize query based on stage and previous results
        stage_query = self._customize_query_for_stage(query, stage, previous_results)
        
        logger.info(f"Executing {stage.value} stage", session_id=session_id)
        
        try:
            if stage == AnalysisStage.DISCOVERY:
                # Use search_repository for discovery
                result = await self.client.search_repositories(
                    messages=[{"role": "user", "content": stage_query}],
                    repositories=repositories,
                    session_id=session_id,
                    genius=True
                )
            else:
                # Use query_repository for analysis, synthesis, implementation
                result = await self.client.query_repositories(
                    messages=[{"role": "user", "content": stage_query}],
                    repositories=repositories,
                    session_id=session_id,
                    genius=True
                )
            
            execution_time = time.time() - stage_start
            
            return StageResult(
                stage=stage,
                success=True,
                content=result.get("message", ""),
                sources=result.get("sources", []),
                session_id=session_id,
                execution_time=execution_time,
                metadata={
                    "query": stage_query,
                    "repositories_count": len(repositories)
                }
            )
            
        except Exception as e:
            execution_time = time.time() - stage_start
            logger.error(f"Stage {stage.value} execution failed: {str(e)}", session_id=session_id)
            
            return StageResult(
                stage=stage,
                success=False,
                content=f"Stage execution failed: {str(e)}",
                sources=[],
                session_id=session_id,
                execution_time=execution_time,
                metadata={"error": str(e), "query": stage_query}
            )
    
    def _customize_query_for_stage(
        self,
        original_query: str,
        stage: AnalysisStage,
        previous_results: List[StageResult]
    ) -> str:
        """Customize query for specific analysis stage, incorporating previous results."""
        
        # Build context from previous successful results
        context = ""
        if previous_results:
            successful_results = [r for r in previous_results if r.success]
            if successful_results:
                context = "\n\nBuilding on previous analysis:\n"
                for result in successful_results:
                    context += f"- {result.stage.value}: {result.content[:200]}...\n"
        
        if stage == AnalysisStage.DISCOVERY:
            return f"""Find relevant files, patterns, and components related to: {original_query}
            
Focus on discovering:
- Key files and directories
- Important patterns and architectures  
- Dependencies and relationships
- Entry points and main components{context}"""
        
        elif stage == AnalysisStage.ANALYSIS:
            return f"""Analyze the architectural patterns and implementation details for: {original_query}
            
Provide deep analysis of:
- How the feature/pattern is implemented
- Key architectural decisions and trade-offs
- Dependencies and relationships between components
- Design patterns and best practices used{context}"""
        
        elif stage == AnalysisStage.SYNTHESIS:
            return f"""Synthesize insights and provide comprehensive understanding of: {original_query}
            
Combine analysis to provide:
- Overall architectural approach
- Key insights and patterns
- Relationships between different aspects
- Unified understanding of the implementation{context}"""
        
        elif stage == AnalysisStage.IMPLEMENTATION:
            return f"""Provide specific implementation guidance for: {original_query}
            
Include:
- Step-by-step implementation approach
- Code examples and patterns to follow
- Common pitfalls and how to avoid them
- Best practices and recommendations{context}"""
        
        return original_query
    
    def _can_run_parallel(self, stage: AnalysisStage, previous_stages: List[AnalysisStage]) -> bool:
        """Determine if a stage can run in parallel with previous stages."""
        # For now, run sequentially to maintain session continuity
        # Future enhancement: implement parallel execution for independent stages
        return False
    
    async def _synthesize_results(
        self,
        stage_results: List[StageResult],
        original_query: str,
        session_id: str
    ) -> str:
        """Synthesize results from all stages into unified response."""
        
        successful_results = [r for r in stage_results if r.success]
        
        if not successful_results:
            return "Pipeline execution completed but no stages were successful."
        
        # Build comprehensive synthesis
        synthesis = f"## Comprehensive Analysis: {original_query}\n\n"
        
        for result in successful_results:
            synthesis += f"### {result.stage.value.title()} Results\n"
            synthesis += f"{result.content}\n\n"
        
        # Add metadata
        synthesis += "### Pipeline Summary\n"
        synthesis += f"- Stages executed: {len(stage_results)}\n"
        synthesis += f"- Successful stages: {len(successful_results)}\n"
        synthesis += f"- Total sources: {sum(len(r.sources) for r in successful_results)}\n"
        synthesis += f"- Session ID: {session_id}\n"
        
        return synthesis


class ResultSynthesizer:
    """Synthesizes results from multiple analysis stages or agents."""
    
    @staticmethod
    def combine_sources(results: List[StageResult]) -> List[Dict[str, Any]]:
        """Combine and deduplicate sources from multiple stage results."""
        all_sources = []
        seen_sources = set()
        
        for result in results:
            for source in result.sources:
                # Create unique identifier for source
                source_id = f"{source.get('filepath', '')}:{source.get('lines', '')}"
                if source_id not in seen_sources:
                    seen_sources.add(source_id)
                    all_sources.append(source)
        
        return all_sources
    
    @staticmethod
    def extract_key_insights(results: List[StageResult]) -> List[str]:
        """Extract key insights from stage results."""
        insights = []
        
        for result in results:
            if result.success and result.content:
                # Simple insight extraction - could be enhanced with NLP
                content_lines = result.content.split('\n')
                for line in content_lines:
                    line = line.strip()
                    if line and (line.startswith('-') or line.startswith('*') or 'key' in line.lower()):
                        insights.append(f"{result.stage.value}: {line}")
        
        return insights[:10]  # Top 10 insights