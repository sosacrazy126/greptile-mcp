#!/usr/bin/env python3
"""
Greptile CLI - Interactive command-line interface for Greptile
This script provides a terminal-based UI to interact with Greptile's API
"""

import os
import sys
import json
import requests
import argparse
import textwrap
import random
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import getpass
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.layout import Layout
from rich import box

# Base URL for Greptile API
BASE_URL = "https://api.greptile.com/v2"

# Config file path
CONFIG_FILE = os.path.expanduser("~/.greptile_config.json")

console = Console()

def generate_mock_answer(query: str, repo_info: str) -> str:
    """Generate a mock answer based on the query"""
    if "main" in query.lower() or "file" in query.lower():
        return f"# Main Files{repo_info}\n\nThe main files in this repository are:\n\n1. **`index.js`** - The entry point for the application\n2. **`src/core/`** - Core functionality modules\n3. **`src/utils/`** - Utility functions\n4. **`src/components/`** - UI components\n5. **`package.json`** - Dependencies and project configuration\n\nThe application follows a modular architecture with clear separation of concerns."
    
    elif "architecture" in query.lower() or "structure" in query.lower():
        return f"# Architecture{repo_info}\n\nThe codebase follows a layered architecture:\n\n1. **Presentation Layer** - UI components and views\n2. **Business Logic Layer** - Core functionality and domain logic\n3. **Data Access Layer** - API clients and data persistence\n\nDependency injection is used throughout the codebase to maintain loose coupling between components."
    
    elif "api" in query.lower() or "endpoint" in query.lower():
        return f"# API Endpoints{repo_info}\n\nThe main API endpoints are:\n\n1. **`/api/v1/users`** - User management\n2. **`/api/v1/auth`** - Authentication and authorization\n3. **`/api/v1/data`** - Data operations\n\nAll endpoints follow RESTful conventions and return JSON responses."
    
    else:
        return f"Based on my analysis of the codebase{repo_info}, I can see that your question relates to the overall structure. The repository is organized into several key directories including `src/`, `tests/`, and `docs/`. The main functionality is implemented in the `src/` directory with clear separation between components, utilities, and core business logic."

def generate_mock_sources(repositories: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Generate mock sources for repository references"""
    sources = []
    
    if not repositories:
        return sources
    
    # Sample file paths and structures
    sample_files = [
        {"path": "index.js", "start": 1, "end": 25, "summary": "Main entry point that initializes the application"},
        {"path": "src/core/main.js", "start": 10, "end": 45, "summary": "Core functionality implementation"},
        {"path": "src/utils/helpers.js", "start": 5, "end": 30, "summary": "Helper utilities for common operations"},
        {"path": "src/components/App.js", "start": 15, "end": 60, "summary": "Main application component"},
        {"path": "package.json", "start": 1, "end": 15, "summary": "Project dependencies and configuration"},
    ]
    
    # Generate 3-5 sources
    num_sources = min(len(sample_files), random.randint(3, 5))
    selected_files = random.sample(sample_files, num_sources)
    
    for repo in repositories[:2]:  # Limit to first 2 repos for simplicity
        for file in selected_files:
            sources.append({
                "repository": repo.get("repository", "owner/repo"),
                "remote": repo.get("remote", "github"),
                "branch": repo.get("branch", "main"),
                "filepath": file["path"],
                "linestart": file["start"],
                "lineend": file["end"],
                "summary": file["summary"]
            })
    
    return sources

@dataclass
class GreptileConfig:
    api_key: str = ""
    github_token: str = ""
    default_remote: str = "github"
    default_repositories: List[Dict[str, str]] = None
    session_id: str = ""
    
    def __post_init__(self):
        if self.default_repositories is None:
            self.default_repositories = []

def load_config() -> GreptileConfig:
    """Load configuration from file or create default"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
                return GreptileConfig(**config_data)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load config file: {e}[/yellow]")
    
    return GreptileConfig()

def save_config(config: GreptileConfig) -> None:
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config.__dict__, f, indent=2)
        os.chmod(CONFIG_FILE, 0o600)  # Secure the file with user-only permissions
    except Exception as e:
        console.print(f"[red]Error saving config: {e}[/red]")

# Set to True to use mock data instead of real API calls (for demo/testing)
USE_MOCK_DATA = False

# Global debug mode flag
DEBUG_MODE = False

def make_api_request(
    endpoint: str, 
    method: str = "GET", 
    data: Optional[Dict[str, Any]] = None,
    config: GreptileConfig = None,
    show_progress: bool = True,
    stream: bool = False
) -> Dict[str, Any]:
    """Make an API request to Greptile"""
    if config is None:
        config = load_config()
    
    # If mock mode is enabled, return mock data
    if USE_MOCK_DATA:
        return get_mock_response(endpoint, data)
    
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json"
    }
    
    if config.github_token:
        headers["X-GitHub-Token"] = config.github_token
    
    url = f"{BASE_URL}/{endpoint.lstrip('/')}"
    
    try:
        if show_progress:
            console.print("[bold blue]Making API request...[/bold blue]")
        
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, stream=stream)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data, stream=stream)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        
        # Handle streaming response if stream=True
        if stream and data and data.get("stream", False):
            return {"message": "Streaming response initiated", "stream": response}
        
        # Handle regular JSON response
        try:
            return response.json()
        except json.JSONDecodeError as e:
            console.print(f"[red]JSON Parse Error: {e}[/red]")
            console.print(f"[yellow]Response Text: {response.text[:100]}...[/yellow]")
            return {"message": "Error parsing API response"}
    except requests.exceptions.RequestException as e:
        console.print(f"[red]API Error: {e}[/red]")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                console.print(f"[red]Response: {error_data}[/red]")
            except:
                console.print(f"[red]Status Code: {e.response.status_code}[/red]")
        return {"message": "API request failed"}

def get_mock_response(endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generate mock responses for demonstration purposes"""
    if endpoint == "repositories" and data:
        # Mock response for indexing a repository
        return {
            "message": "Repository indexing initiated",
            "statusEndpoint": f"https://api.greptile.com/v2/repositories/{data['remote']}%3A{data['branch']}%3A{data['repository']}"
        }
    
    elif endpoint.startswith("repositories/"):
        # Mock response for repository status
        repo_parts = endpoint.split("/")[1].split("%3A")
        if len(repo_parts) >= 3:
            remote, branch, repo = repo_parts[0], repo_parts[1], repo_parts[2]
            return {
                "repository": repo,
                "remote": remote,
                "branch": branch,
                "private": False,
                "status": "indexed",
                "filesProcessed": 256,
                "numFiles": 256,
                "sha": "abc123def456"
            }
    
    elif endpoint == "query" and data and data.get("messages"):
        # Mock response for chat query
        query = data["messages"][-1]["content"]
        repo_info = ""
        if data.get("repositories"):
            repo_info = f" in {', '.join([r['repository'] for r in data['repositories']])}"
        
        return {
            "message": generate_mock_answer(query, repo_info),
            "sources": generate_mock_sources(data.get("repositories", []))
        }
    
    elif endpoint == "search" and data and data.get("messages"):
        # Mock response for search
        return {
            "sources": generate_mock_sources(data.get("repositories", []))
        }
    
    # Default mock response
    return {"message": "Mock response for endpoint: " + endpoint}

def setup_credentials() -> GreptileConfig:
    """Setup or update API credentials"""
    config = load_config()
    
    console.print(Panel.fit(
        "[bold]Greptile API Credentials Setup[/bold]\n\n"
        "You'll need two tokens to use Greptile:\n"
        "1. A Greptile API key from https://app.greptile.com/login\n"
        "2. A GitHub/GitLab token with repository access permissions"
    ))
    
    # Get Greptile API key
    if config.api_key:
        show_current = Confirm.ask("You have an existing Greptile API key. Show it?")
        if show_current:
            console.print(f"Current API key: [cyan]{config.api_key}[/cyan]")
        
        update = Confirm.ask("Update your Greptile API key?")
        if update:
            config.api_key = Prompt.ask("Enter your Greptile API key", password=True)
    else:
        config.api_key = Prompt.ask("Enter your Greptile API key", password=True)
    
    # Get GitHub/GitLab token
    if config.github_token:
        show_current = Confirm.ask("You have an existing GitHub/GitLab token. Show it?")
        if show_current:
            console.print(f"Current GitHub/GitLab token: [cyan]{config.github_token}[/cyan]")
        
        update = Confirm.ask("Update your GitHub/GitLab token?")
        if update:
            config.github_token = Prompt.ask("Enter your GitHub/GitLab token", password=True)
    else:
        config.github_token = Prompt.ask("Enter your GitHub/GitLab token", password=True)
    
    # Save the config
    save_config(config)
    console.print("[green]Credentials saved successfully![/green]")
    
    return config

def manage_repositories(config: GreptileConfig) -> None:
    """Manage repositories for indexing and querying"""
    while True:
        console.clear()
        console.print(Panel.fit("[bold]Repository Management[/bold]"))
        
        # Display current repositories
        if config.default_repositories:
            table = Table(title="Your Repositories")
            table.add_column("Remote", style="cyan")
            table.add_column("Repository", style="green")
            table.add_column("Branch", style="yellow")
            
            for idx, repo in enumerate(config.default_repositories):
                table.add_row(
                    repo.get("remote", "github"),
                    repo.get("repository", ""),
                    repo.get("branch", "main")
                )
            
            console.print(table)
        else:
            console.print("[yellow]No repositories configured yet.[/yellow]")
        
        # Options
        console.print("\n[bold]Options:[/bold]")
        console.print("1. Add a repository")
        console.print("2. Remove a repository")
        console.print("3. Index a repository")
        console.print("4. Check repository status")
        console.print("5. Back to main menu")
        
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4", "5"])
        
        if choice == "1":
            # Add a repository
            remote = Prompt.ask("Remote service", choices=["github", "gitlab"], default="github")
            repository = Prompt.ask("Repository (format: owner/repository)")
            branch = Prompt.ask("Branch", default="main")
            
            new_repo = {
                "remote": remote,
                "repository": repository,
                "branch": branch
            }
            
            config.default_repositories.append(new_repo)
            save_config(config)
            console.print("[green]Repository added successfully![/green]")
        
        elif choice == "2":
            # Remove a repository
            if not config.default_repositories:
                console.print("[yellow]No repositories to remove.[/yellow]")
                continue
            
            console.print("\n[bold]Select a repository to remove:[/bold]")
            for idx, repo in enumerate(config.default_repositories):
                console.print(f"{idx+1}. {repo['remote']}:{repo['repository']} ({repo['branch']})")
            
            console.print(f"{len(config.default_repositories)+1}. Cancel")
            
            choices = [str(i+1) for i in range(len(config.default_repositories)+1)]
            idx_choice = Prompt.ask("Choose a repository", choices=choices)
            
            if int(idx_choice) <= len(config.default_repositories):
                removed = config.default_repositories.pop(int(idx_choice)-1)
                save_config(config)
                console.print(f"[green]Removed {removed['repository']}[/green]")
        
        elif choice == "3":
            # Index a repository
            if not config.default_repositories:
                console.print("[yellow]No repositories configured. Add one first.[/yellow]")
                continue
            
            console.print("\n[bold]Select a repository to index:[/bold]")
            for idx, repo in enumerate(config.default_repositories):
                console.print(f"{idx+1}. {repo['remote']}:{repo['repository']} ({repo['branch']})")
            
            console.print(f"{len(config.default_repositories)+1}. Cancel")
            
            choices = [str(i+1) for i in range(len(config.default_repositories)+1)]
            idx_choice = Prompt.ask("Choose a repository", choices=choices)
            
            if int(idx_choice) <= len(config.default_repositories):
                repo = config.default_repositories[int(idx_choice)-1]
                
                # Confirm indexing
                reload = Confirm.ask("Reindex if already indexed?", default=True)
                notify = Confirm.ask("Receive notification upon completion?", default=True)
                
                # Make API request to index
                data = {
                    "remote": repo["remote"],
                    "repository": repo["repository"],
                    "branch": repo["branch"],
                    "reload": reload,
                    "notify": notify
                }
                
                response = make_api_request("repositories", "POST", data, config)
                
                if response:
                    console.print("[green]Repository indexing initiated![/green]")
                    console.print(f"Message: {response.get('message', 'No message')}")
                    console.print(f"Status endpoint: {response.get('statusEndpoint', 'No status endpoint')}")
                
                input("\nPress Enter to continue...")
        
        elif choice == "4":
            # Check repository status
            if not config.default_repositories:
                console.print("[yellow]No repositories configured. Add one first.[/yellow]")
                continue
            
            console.print("\n[bold]Select a repository to check status:[/bold]")
            for idx, repo in enumerate(config.default_repositories):
                console.print(f"{idx+1}. {repo['remote']}:{repo['repository']} ({repo['branch']})")
            
            console.print(f"{len(config.default_repositories)+1}. Cancel")
            
            choices = [str(i+1) for i in range(len(config.default_repositories)+1)]
            idx_choice = Prompt.ask("Choose a repository", choices=choices)
            
            if int(idx_choice) <= len(config.default_repositories):
                repo = config.default_repositories[int(idx_choice)-1]
                
                # Format repository ID
                repo_id = f"{repo['remote']}:{repo['branch']}:{repo['repository']}"
                
                # Make API request to get status
                response = make_api_request(f"repositories/{repo_id}", "GET", None, config)
                
                if response:
                    status_panel = Panel(
                        f"[bold]Repository:[/bold] {response.get('repository', 'Unknown')}\n"
                        f"[bold]Remote:[/bold] {response.get('remote', 'Unknown')}\n"
                        f"[bold]Branch:[/bold] {response.get('branch', 'Unknown')}\n"
                        f"[bold]Private:[/bold] {response.get('private', False)}\n"
                        f"[bold]Status:[/bold] {response.get('status', 'Unknown')}\n"
                        f"[bold]Files Processed:[/bold] {response.get('filesProcessed', 0)}\n"
                        f"[bold]Total Files:[/bold] {response.get('numFiles', 0)}\n"
                        f"[bold]SHA:[/bold] {response.get('sha', 'Unknown')}",
                        title="Repository Status"
                    )
                    console.print(status_panel)
                
                input("\nPress Enter to continue...")
        
        elif choice == "5":
            # Back to main menu
            break

def chat_with_repo(config: GreptileConfig) -> None:
    """Chat with repositories using natural language queries"""
    if not config.default_repositories:
        console.print("[yellow]No repositories configured. Please add repositories first.[/yellow]")
        input("\nPress Enter to continue...")
        return
    
    # Select repositories to query
    console.print(Panel.fit("[bold]Chat with Repositories[/bold]"))
    console.print("[bold]Select repositories to query (space-separated numbers):[/bold]")
    
    for idx, repo in enumerate(config.default_repositories):
        console.print(f"{idx+1}. {repo['remote']}:{repo['repository']} ({repo['branch']})")
    
    repo_choices = Prompt.ask("Enter repository numbers (e.g., '1 3')")
    selected_indices = [int(idx)-1 for idx in repo_choices.split() if idx.isdigit() and int(idx) <= len(config.default_repositories)]
    
    if not selected_indices:
        console.print("[yellow]No valid repositories selected.[/yellow]")
        input("\nPress Enter to continue...")
        return
    
    selected_repos = [config.default_repositories[idx] for idx in selected_indices]
    
    # Display selected repositories
    console.print("[green]Selected repositories:[/green]")
    for repo in selected_repos:
        console.print(f"- {repo['remote']}:{repo['repository']} ({repo['branch']})")
    
    # Chat options
    genius_mode = Confirm.ask("Enable genius mode? (smarter but slower)", default=False)
    stream_mode = Confirm.ask("Enable streaming mode?", default=False)
    
    if stream_mode:
        console.print("[yellow]Note: Streaming mode is experimental and may not work with all API keys.[/yellow]")
    
    # Start chat session
    messages = []
    
    while True:
        console.print("\n[bold cyan]Ask a question about the codebase (or type 'exit' to quit):[/bold cyan]")
        query = console.input("> ")
        
        if query.lower() in ["exit", "quit", "q"]:
            break
        
        # Add message to history
        message_id = f"msg_{len(messages) + 1}"
        messages.append({
            "id": message_id,
            "content": query,
            "role": "user"
        })
        
        # Prepare API request
        data = {
            "messages": messages,
            "repositories": selected_repos,
            "sessionId": config.session_id or None,
            "stream": stream_mode,
            "genius": genius_mode
        }
        
        # Make API request
        console.print("\n[bold blue]Greptile is thinking...[/bold blue]")
        
        if stream_mode:
            # Handle streaming response
            try:
                response = make_api_request("query", "POST", data, config, show_progress=False, stream=True)
                
                if "stream" in response:
                    stream_response = response["stream"]
                    console.print("\n[bold green]Streaming response:[/bold green]")
                    
                    # Process the streaming response
                    full_response = ""
                    for line in stream_response.iter_lines():
                        if line:
                            try:
                                # Try to parse each line as JSON
                                line_data = json.loads(line.decode('utf-8').lstrip('data: '))
                                if "message" in line_data:
                                    # Print the message part
                                    console.print(line_data["message"], end="")
                                    full_response += line_data["message"]
                            except json.JSONDecodeError:
                                # If not JSON, just print the raw line
                                decoded_line = line.decode('utf-8')
                                if decoded_line.startswith('data: '):
                                    decoded_line = decoded_line[6:]
                                console.print(decoded_line)
                                full_response += decoded_line
                    
                    # Create a response object with the full streamed content
                    response = {"message": full_response, "sources": []}
                else:
                    # Fallback to non-streaming if stream object not returned
                    console.print("[yellow]Streaming not supported by API, falling back to standard mode[/yellow]")
            except Exception as e:
                console.print(f"[red]Error in streaming mode: {e}[/red]")
                console.print("[yellow]Falling back to standard mode[/yellow]")
                # Fallback to non-streaming mode
                data["stream"] = False
                response = make_api_request("query", "POST", data, config, show_progress=False)
        else:
            # Standard non-streaming request
            response = make_api_request("query", "POST", data, config, show_progress=False)
        
        if response:
            # Display the response
            answer = response.get("message", "No answer received")
            sources = response.get("sources", [])
            
            # Add assistant response to messages if not empty
            if answer and answer != "No answer received":
                messages.append({
                    "id": f"msg_{len(messages) + 1}",
                    "content": answer,
                    "role": "assistant"
                })
            
            # Display answer
            if answer and answer != "No answer received":
                console.print("\n[bold green]Greptile's Answer:[/bold green]")
                try:
                    console.print(Panel(Markdown(answer), border_style="green"))
                except Exception as e:
                    # Fallback if markdown parsing fails
                    console.print(Panel(answer, border_style="green"))
            else:
                console.print("\n[bold yellow]No answer received from Greptile[/bold yellow]")
                if "error" in response:
                    console.print(f"[red]Error: {response['error']}[/red]")
            
            # Display sources if available
            if sources:
                console.print("\n[bold yellow]Sources:[/bold yellow]")
                sources_table = Table(box=box.SIMPLE)
                sources_table.add_column("Repository", style="cyan")
                sources_table.add_column("File", style="green")
                sources_table.add_column("Lines", style="yellow")
                sources_table.add_column("Summary", style="white", max_width=40)
                
                for source in sources:
                    sources_table.add_row(
                        f"{source.get('remote', '')}:{source.get('repository', '')}",
                        source.get('filepath', ''),
                        f"{source.get('linestart', '')} - {source.get('lineend', '')}",
                        textwrap.shorten(source.get('summary', ''), width=40, placeholder="...")
                    )
                
                console.print(sources_table)
            elif not answer or answer == "No answer received":
                console.print("\n[yellow]No sources found. This could indicate an issue with the API response or that the repository hasn't been properly indexed.[/yellow]")
    
    # Save session ID for future use
    if response and not config.session_id:
        save_session = Confirm.ask("Save this chat session for future reference?", default=True)
        if save_session and "sessionId" in response:
            config.session_id = response["sessionId"]
            save_config(config)
            console.print("[green]Session saved![/green]")

def search_repo(config: GreptileConfig) -> None:
    """Search repositories without generating answers"""
    if not config.default_repositories:
        console.print("[yellow]No repositories configured. Please add repositories first.[/yellow]")
        input("\nPress Enter to continue...")
        return
    
    # Select repositories to search
    console.print(Panel.fit("[bold]Search Repositories[/bold]"))
    console.print("[bold]Select repositories to search (space-separated numbers):[/bold]")
    
    for idx, repo in enumerate(config.default_repositories):
        console.print(f"{idx+1}. {repo['remote']}:{repo['repository']} ({repo['branch']})")
    
    repo_choices = Prompt.ask("Enter repository numbers (e.g., '1 3')")
    selected_indices = [int(idx)-1 for idx in repo_choices.split() if idx.isdigit() and int(idx) <= len(config.default_repositories)]
    
    if not selected_indices:
        console.print("[yellow]No valid repositories selected.[/yellow]")
        input("\nPress Enter to continue...")
        return
    
    selected_repos = [config.default_repositories[idx] for idx in selected_indices]
    
    # Display selected repositories
    console.print("[green]Selected repositories:[/green]")
    for repo in selected_repos:
        console.print(f"- {repo['remote']}:{repo['repository']} ({repo['branch']})")
    
    # Get search query
    console.print("\n[bold cyan]Enter your search query:[/bold cyan]")
    query = console.input("> ")
    
    if not query:
        console.print("[yellow]Empty query. Returning to main menu.[/yellow]")
        return
    
    # Prepare API request
    data = {
        "messages": [{
            "id": "search_query",
            "content": query,
            "role": "user"
        }],
        "repositories": selected_repos
    }
    
    # Make API request
    response = make_api_request("search", "POST", data, config)
    
    if response:
        # Display sources
        sources = response.get("sources", [])
        
        if sources:
            console.print("\n[bold green]Search Results:[/bold green]")
            sources_table = Table(box=box.SIMPLE)
            sources_table.add_column("Repository", style="cyan")
            sources_table.add_column("File", style="green")
            sources_table.add_column("Lines", style="yellow")
            sources_table.add_column("Summary", style="white")
            
            for source in sources:
                sources_table.add_row(
                    f"{source.get('remote', '')}:{source.get('repository', '')}",
                    source.get('filepath', ''),
                    f"{source.get('linestart', '')} - {source.get('lineend', '')}",
                    textwrap.shorten(source.get('summary', ''), width=50, placeholder="...")
                )
            
            console.print(sources_table)
        else:
            console.print("[yellow]No results found.[/yellow]")
    
    input("\nPress Enter to continue...")

def show_help() -> None:
    """Display help information"""
    help_text = """
# Greptile CLI Help

## Overview
Greptile is a powerful code search and understanding tool that allows you to index and query repositories using natural language.

## Workflow
1. **Setup Credentials**: Configure your Greptile API key and GitHub/GitLab token
2. **Manage Repositories**: Add repositories you want to work with
3. **Index Repositories**: Submit repositories for indexing
4. **Chat with Repositories**: Ask natural language questions about your code
5. **Search Repositories**: Find relevant code without generating answers

## Tips
- Indexing may take some time for large repositories
- Use genius mode for complex queries (but it's slower)
- Be specific in your questions for better results
- You can query multiple repositories at once

## More Information
Visit https://www.greptile.com/docs for detailed documentation
    """
    
    console.print(Markdown(help_text))
    input("\nPress Enter to continue...")

def main() -> None:
    """Main function for the Greptile CLI"""
    parser = argparse.ArgumentParser(description="Greptile CLI - Interactive command-line interface for Greptile")
    parser.add_argument("--setup", action="store_true", help="Setup API credentials")
    parser.add_argument("--chat", action="store_true", help="Go directly to chat interface")
    parser.add_argument("--search", action="store_true", help="Go directly to search interface")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode for verbose output")
    args = parser.parse_args()
    
    # Set debug mode globally
    global DEBUG_MODE
    DEBUG_MODE = args.debug
    
    # Load configuration
    config = load_config()
    
    # If setup flag is provided, run setup and exit
    if args.setup:
        setup_credentials()
        return
    
    # Check if credentials are configured
    if not config.api_key or not config.github_token:
        console.print("[yellow]API credentials not configured. Running setup...[/yellow]")
        config = setup_credentials()
    
    # Direct access to chat or search if specified
    if args.chat:
        chat_with_repo(config)
        return
    elif args.search:
        search_repo(config)
        return
    
    # Main menu loop
    while True:
        console.clear()
        console.print(Panel.fit(
            "[bold cyan]Greptile CLI[/bold cyan]\n"
            "Interactive command-line interface for Greptile",
            title="Welcome"
        ))
        
        console.print("[bold]Main Menu:[/bold]")
        console.print("1. Setup/Update API Credentials")
        console.print("2. Manage Repositories")
        console.print("3. [bold green]Chat with Repositories[/bold green]")
        console.print("4. Search Repositories")
        console.print("5. Help")
        console.print("6. Exit")
        
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4", "5", "6"])
        
        if choice == "1":
            config = setup_credentials()
        elif choice == "2":
            manage_repositories(config)
        elif choice == "3":
            chat_with_repo(config)
        elif choice == "4":
            search_repo(config)
        elif choice == "5":
            show_help()
        elif choice == "6":
            console.print("[bold green]Goodbye![/bold green]")
            break

if __name__ == "__main__":
    try:
        # Display banner on startup
        console.print(Panel.fit(
            "[bold cyan]Greptile CLI[/bold cyan]\n"
            "A command-line interface for Greptile's code search and understanding API\n"
            "Run with --help to see available options",
            title="Welcome", border_style="cyan"
        ))
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]Program interrupted by user. Exiting...[/bold red]")
        sys.exit(0)