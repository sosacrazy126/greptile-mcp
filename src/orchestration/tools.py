"""
Orchestration Tools for Greptile-MCP

High-level tools that coordinate multiple analysis stages using the Claude Code 
sub-agent orchestration pattern.
"""

import json
from typing import Optional, List, Dict, Any

from .pipeline import MultiStageCoordinator, AnalysisStage, PipelineConfig
from .synthesis import CrossRepositorySynthesizer, PatternAnalyzer
from ..utils import GreptileClient
from ..logging_config import logger


async def analyze_codebase_feature(
    client: GreptileClient,
    feature: str,
    repositories: Optional[str] = None,
    session_id: Optional[str] = None,
    analysis_depth: str = "comprehensive",
    include_implementation: bool = True,
    include_examples: bool = False
) -> str:
    """
    Autonomous codebase feature analysis using multi-stage orchestration.
    
    Implements Claude Code sub-agent pattern:
    1. Lead agent analyzes the feature request
    2. Spawns specialized sub-agents for discovery, analysis, implementation
    3. Coordinates parallel execution where possible
    4. Synthesizes results into comprehensive response
    
    Args:
        client: GreptileClient instance
        feature: Feature or pattern to analyze
        repositories: JSON string of repositories (optional if session exists)
        session_id: Optional session ID for context continuity
        analysis_depth: "basic", "comprehensive", or "expert"
        include_implementation: Include implementation guidance
        include_examples: Include code examples in response
    
    Returns:
        JSON string with comprehensive analysis
    """
    
    # Parse repositories if provided
    repositories_list = []
    if repositories:
        try:
            repositories_list = json.loads(repositories)
        except json.JSONDecodeError:
            return json.dumps({
                "error": "Invalid repositories JSON format",
                "type": "ValidationError"
            })
    elif session_id is None:
        return json.dumps({
            "error": "Either repositories or session_id must be provided",
            "type": "ValidationError"
        })
    
    # Configure pipeline based on analysis depth
    config = PipelineConfig()
    
    if analysis_depth == "basic":
        stages = [AnalysisStage.DISCOVERY, AnalysisStage.ANALYSIS]
        config.stage_timeout = 60.0
    elif analysis_depth == "expert":
        stages = [AnalysisStage.DISCOVERY, AnalysisStage.ANALYSIS, 
                 AnalysisStage.SYNTHESIS, AnalysisStage.IMPLEMENTATION]
        config.stage_timeout = 180.0
        config.include_implementation_examples = include_examples
    else:  # comprehensive
        stages = [AnalysisStage.DISCOVERY, AnalysisStage.ANALYSIS, AnalysisStage.IMPLEMENTATION]
        config.stage_timeout = 120.0
    
    if not include_implementation:
        stages = [s for s in stages if s != AnalysisStage.IMPLEMENTATION]
    
    logger.info(
        f"Starting feature analysis: {feature}",
        session_id=session_id,
        analysis_depth=analysis_depth,
        stages=[s.value for s in stages]
    )
    
    try:
        # Initialize coordinator with Claude Code orchestration pattern
        coordinator = MultiStageCoordinator(client, config)
        
        # Execute orchestrated pipeline
        result = await coordinator.execute_pipeline(
            query=f"Analyze the {feature} feature/pattern implementation",
            repositories=repositories_list,
            session_id=session_id,
            stages=stages
        )
        
        # Enhance result with orchestration metadata
        result["orchestration_type"] = "feature_analysis"
        result["feature_analyzed"] = feature
        result["analysis_depth"] = analysis_depth
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Feature analysis failed: {str(e)}", session_id=session_id)
        return json.dumps({
            "error": f"Feature analysis failed: {str(e)}",
            "type": type(e).__name__,
            "session_id": session_id
        })


async def compare_codebase_patterns(
    client: GreptileClient,
    pattern_focus: str,
    repositories: str,  # Required for multi-repo comparison
    session_id: Optional[str] = None,
    comparison_depth: str = "architectural"
) -> str:
    """
    Cross-repository pattern comparison using specialized synthesis agents.
    
    Implements orchestration pattern for multi-repository analysis:
    1. Lead agent decomposes comparison task
    2. Spawns analysis agents for each repository
    3. Spawns synthesis agent for cross-repository insights
    4. Coordinates result integration
    
    Args:
        client: GreptileClient instance  
        pattern_focus: Pattern or aspect to compare across repositories
        repositories: JSON string of repositories to compare
        session_id: Optional session ID for context continuity
        comparison_depth: "basic", "architectural", or "implementation"
    
    Returns:
        JSON string with comparative analysis
    """
    
    # Parse repositories
    try:
        repositories_list = json.loads(repositories)
        if len(repositories_list) < 2:
            return json.dumps({
                "error": "At least 2 repositories required for comparison",
                "type": "ValidationError"
            })
    except json.JSONDecodeError:
        return json.dumps({
            "error": "Invalid repositories JSON format", 
            "type": "ValidationError"
        })
    
    logger.info(
        f"Starting cross-repository comparison: {pattern_focus}",
        session_id=session_id,
        repositories_count=len(repositories_list),
        comparison_depth=comparison_depth
    )
    
    try:
        # Initialize cross-repository synthesizer
        synthesizer = CrossRepositorySynthesizer(client)
        
        # Execute comparison using orchestrated sub-agents
        result = await synthesizer.compare_patterns(
            pattern_focus=pattern_focus,
            repositories=repositories_list,
            session_id=session_id,
            depth=comparison_depth
        )
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Pattern comparison failed: {str(e)}", session_id=session_id)
        return json.dumps({
            "error": f"Pattern comparison failed: {str(e)}",
            "type": type(e).__name__,
            "session_id": session_id
        })


async def explore_codebase_autonomous(
    client: GreptileClient,
    starting_point: str,
    repositories: Optional[str] = None,
    exploration_depth: int = 3,
    session_id: Optional[str] = None
) -> str:
    """
    Autonomous codebase exploration using recursive sub-agent pattern.
    
    Implements recursive exploration pattern:
    1. Lead agent analyzes starting point
    2. Spawns exploration sub-agents for discovered patterns
    3. Each sub-agent recursively explores their findings
    4. Coordinates depth-limited exploration to prevent infinite recursion
    5. Synthesizes exploration results into comprehensive map
    
    Args:
        client: GreptileClient instance
        starting_point: Initial focus for exploration
        repositories: JSON string of repositories (optional if session exists)
        exploration_depth: Maximum recursion depth (1-5)
        session_id: Optional session ID for context continuity
        
    Returns:
        JSON string with exploration results
    """
    
    # Validate exploration depth
    if exploration_depth < 1 or exploration_depth > 5:
        return json.dumps({
            "error": "Exploration depth must be between 1 and 5",
            "type": "ValidationError"
        })
    
    # Parse repositories if provided
    repositories_list = []
    if repositories:
        try:
            repositories_list = json.loads(repositories)
        except json.JSONDecodeError:
            return json.dumps({
                "error": "Invalid repositories JSON format",
                "type": "ValidationError"
            })
    elif session_id is None:
        return json.dumps({
            "error": "Either repositories or session_id must be provided",
            "type": "ValidationError"
        })
    
    logger.info(
        f"Starting autonomous exploration: {starting_point}",
        session_id=session_id,
        exploration_depth=exploration_depth
    )
    
    try:
        # Initialize pattern analyzer for recursive exploration
        analyzer = PatternAnalyzer(client)
        
        # Execute autonomous exploration
        result = await analyzer.explore_recursive(
            starting_point=starting_point,
            repositories=repositories_list,
            session_id=session_id,
            max_depth=exploration_depth
        )
        
        # Enhance with exploration metadata
        result["exploration_type"] = "autonomous_recursive"
        result["starting_point"] = starting_point
        result["max_depth"] = exploration_depth
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Autonomous exploration failed: {str(e)}", session_id=session_id)
        return json.dumps({
            "error": f"Autonomous exploration failed: {str(e)}",
            "type": type(e).__name__,
            "session_id": session_id
        })