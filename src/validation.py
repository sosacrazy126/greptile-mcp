"""
Input validation and error handling utilities for Greptile MCP Server.

This module provides comprehensive validation for all input parameters and
standardized error handling patterns.
"""

import re
import json
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ValidationError(Exception):
    """Custom exception for validation errors."""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(message)


class RemoteType(Enum):
    """Supported repository remote types."""
    GITHUB = "github"
    GITLAB = "gitlab"


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    
    def add_error(self, error: str):
        """Add an error to the validation result."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Add a warning to the validation result."""
        self.warnings.append(warning)


class InputValidator:
    """Comprehensive input validation for all MCP tools."""
    
    # Repository name pattern: owner/repo
    REPO_PATTERN = re.compile(r'^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$')
    
    # Branch name pattern (Git-compatible)
    BRANCH_PATTERN = re.compile(r'^[a-zA-Z0-9._/-]+$')
    
    # Session ID pattern (UUID format, case-insensitive)
    SESSION_ID_PATTERN = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')
    
    @staticmethod
    def validate_remote(remote: str) -> ValidationResult:
        """Validate repository remote type."""
        result = ValidationResult(True, [], [])
        
        if not remote:
            result.add_error("Remote cannot be empty")
            return result
        
        if not isinstance(remote, str):
            result.add_error(f"Remote must be a string, got {type(remote).__name__}")
            return result
        
        remote_lower = remote.lower()
        valid_remotes = [r.value for r in RemoteType]

        if remote_lower not in valid_remotes:
            result.add_error(f"Remote must be one of: {', '.join(valid_remotes)}")
        elif remote != remote_lower:
            result.add_warning(f"Remote case will be normalized: '{remote}' -> '{remote_lower}'")
        
        return result
    
    @staticmethod
    def validate_repository(repository: str) -> ValidationResult:
        """Validate repository name format."""
        result = ValidationResult(True, [], [])
        
        if not repository:
            result.add_error("Repository cannot be empty")
            return result
        
        if not isinstance(repository, str):
            result.add_error(f"Repository must be a string, got {type(repository).__name__}")
            return result
        
        if not InputValidator.REPO_PATTERN.match(repository):
            result.add_error(
                f"Repository must be in 'owner/repo' format. "
                f"Got: '{repository}'"
            )
        
        if len(repository) > 100:
            result.add_error("Repository name too long (max 100 characters)")
        
        # Check for common issues
        if repository.startswith('/') or repository.endswith('/'):
            result.add_error("Repository name cannot start or end with '/'")
        
        if '//' in repository:
            result.add_error("Repository name cannot contain consecutive '/' characters")
        
        return result
    
    @staticmethod
    def validate_branch(branch: str) -> ValidationResult:
        """Validate branch name."""
        result = ValidationResult(True, [], [])
        
        if not branch:
            result.add_error("Branch cannot be empty")
            return result
        
        if not isinstance(branch, str):
            result.add_error(f"Branch must be a string, got {type(branch).__name__}")
            return result
        
        if not InputValidator.BRANCH_PATTERN.match(branch):
            result.add_error(
                f"Branch name contains invalid characters. "
                f"Got: '{branch}'"
            )
        
        if len(branch) > 250:
            result.add_error("Branch name too long (max 250 characters)")
        
        # Git branch name restrictions
        if branch.startswith('.') or branch.endswith('.'):
            result.add_error("Branch name cannot start or end with '.'")
        
        if branch.startswith('-') or branch.endswith('-'):
            result.add_error("Branch name cannot start or end with '-'")
        
        if '..' in branch:
            result.add_error("Branch name cannot contain '..'")
        
        return result
    
    @staticmethod
    def validate_query(query: str) -> ValidationResult:
        """Validate search/query string."""
        result = ValidationResult(True, [], [])
        
        if not query:
            result.add_error("Query cannot be empty")
            return result
        
        if not isinstance(query, str):
            result.add_error(f"Query must be a string, got {type(query).__name__}")
            return result
        
        query_stripped = query.strip()
        if not query_stripped:
            result.add_error("Query cannot be only whitespace")
            return result
        
        if len(query_stripped) < 3:
            result.add_warning("Very short queries may not return useful results")
        
        if len(query) > 2000:
            result.add_error("Query too long (max 2000 characters)")
        
        # Check for potential issues
        if query.count('"') % 2 != 0:
            result.add_warning("Unmatched quotes in query may affect search results")
        
        return result
    
    @staticmethod
    def validate_repositories_json(repositories_json: str) -> Tuple[ValidationResult, List[Dict[str, str]]]:
        """Validate and parse repositories JSON string."""
        result = ValidationResult(True, [], [])
        repositories = []
        
        if not repositories_json:
            result.add_error("Repositories JSON cannot be empty")
            return result, repositories
        
        if not isinstance(repositories_json, str):
            result.add_error(f"Repositories must be a JSON string, got {type(repositories_json).__name__}")
            return result, repositories
        
        # Parse JSON
        try:
            repositories = json.loads(repositories_json)
        except json.JSONDecodeError as e:
            result.add_error(f"Invalid JSON format: {str(e)}")
            return result, repositories
        
        # Validate structure
        if not isinstance(repositories, list):
            result.add_error("Repositories must be a JSON array")
            return result, repositories
        
        if not repositories:
            result.add_error("Repositories array cannot be empty")
            return result, repositories
        
        if len(repositories) > 10:
            result.add_error("Too many repositories (max 10)")
            result.add_warning("Large numbers of repositories may slow down queries")
        
        # Validate each repository
        for i, repo in enumerate(repositories):
            if not isinstance(repo, dict):
                result.add_error(f"Repository {i} must be an object")
                continue
            
            # Required fields
            required_fields = ['remote', 'repository', 'branch']
            for field in required_fields:
                if field not in repo:
                    result.add_error(f"Repository {i} missing required field: {field}")
                    continue
                
                # Validate individual fields
                if field == 'remote':
                    field_result = InputValidator.validate_remote(repo[field])
                elif field == 'repository':
                    field_result = InputValidator.validate_repository(repo[field])
                elif field == 'branch':
                    field_result = InputValidator.validate_branch(repo[field])
                
                if not field_result.is_valid:
                    for error in field_result.errors:
                        result.add_error(f"Repository {i}.{field}: {error}")
                
                for warning in field_result.warnings:
                    result.add_warning(f"Repository {i}.{field}: {warning}")
        
        return result, repositories
    
    @staticmethod
    def validate_session_id(session_id: Optional[str]) -> ValidationResult:
        """Validate session ID format."""
        result = ValidationResult(True, [], [])
        
        if session_id is None:
            return result  # Optional field
        
        if not isinstance(session_id, str):
            result.add_error(f"Session ID must be a string, got {type(session_id).__name__}")
            return result
        
        # Normalize the session ID for validation (trim whitespace, normalize case)
        normalized_session_id = session_id.strip()
        
        if not InputValidator.SESSION_ID_PATTERN.match(normalized_session_id):
            result.add_error(
                f"Session ID must be a valid UUID format (e.g., '12345678-1234-1234-1234-123456789abc'). "
                f"Got: '{session_id}'"
            )
        
        return result
    
    @staticmethod
    def validate_timeout(timeout: Optional[float]) -> ValidationResult:
        """Validate timeout value."""
        result = ValidationResult(True, [], [])
        
        if timeout is None:
            return result  # Optional field
        
        if not isinstance(timeout, (int, float)):
            result.add_error(f"Timeout must be a number, got {type(timeout).__name__}")
            return result
        
        if timeout <= 0:
            result.add_error("Timeout must be positive")
        
        if timeout > 300:  # 5 minutes
            result.add_warning("Very long timeout may cause client disconnection")
        
        if timeout < 1:
            result.add_warning("Very short timeout may cause premature failures")
        
        return result
    
    @staticmethod
    def validate_messages_json(messages_json: Optional[str]) -> Tuple[ValidationResult, Optional[List[Dict[str, Any]]]]:
        """Validate and parse messages JSON string."""
        result = ValidationResult(True, [], [])
        
        if messages_json is None:
            return result, None
        
        if not isinstance(messages_json, str):
            result.add_error(f"Messages must be a JSON string, got {type(messages_json).__name__}")
            return result, None
        
        # Parse JSON
        try:
            messages = json.loads(messages_json)
        except json.JSONDecodeError as e:
            result.add_error(f"Invalid JSON format: {str(e)}")
            return result, None
        
        # Validate structure
        if not isinstance(messages, list):
            result.add_error("Messages must be a JSON array")
            return result, None
        
        if len(messages) > 50:
            result.add_warning("Large message history may slow down processing")
        
        # Validate each message
        for i, msg in enumerate(messages):
            if not isinstance(msg, dict):
                result.add_error(f"Message {i} must be an object")
                continue
            
            if 'role' not in msg:
                result.add_error(f"Message {i} missing required field: role")
            elif msg['role'] not in ['user', 'assistant', 'system']:
                result.add_error(f"Message {i} has invalid role: {msg['role']}")
            
            if 'content' not in msg:
                result.add_error(f"Message {i} missing required field: content")
            elif not isinstance(msg['content'], str):
                result.add_error(f"Message {i} content must be a string")
            elif not msg['content'].strip():
                result.add_error(f"Message {i} content cannot be empty")
        
        return result, messages


def create_error_response(error: str, error_type: str = "ValidationError", **extra_fields) -> str:
    """Create a standardized error response."""
    response = {
        "error": error,
        "type": error_type,
        **extra_fields
    }
    return json.dumps(response)


def create_validation_error_response(validation_result: ValidationResult, **extra_fields) -> str:
    """Create an error response from validation results."""
    error_message = "; ".join(validation_result.errors)
    if validation_result.warnings:
        warning_message = "; ".join(validation_result.warnings)
        error_message += f" (Warnings: {warning_message})"
    
    return create_error_response(
        error_message,
        "ValidationError",
        **extra_fields
    )
