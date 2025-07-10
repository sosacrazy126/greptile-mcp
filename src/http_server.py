"""
FastAPI HTTP server for Greptile MCP tools.
Provides JSON-RPC 2.0 interface to access MCP functionality via HTTP.
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from typing import Dict, Any, Optional, Union, List
import json
import asyncio
import os
import time
import logging
from contextlib import asynccontextmanager
from collections import defaultdict

# Import our refactored MCP components
from src.services.greptile_service import GreptileService
from src.services.session_service import SessionService
from src.handlers.index_handler import IndexHandler
from src.handlers.query_handler import QueryHandler
from src.handlers.search_handler import SearchHandler
from src.handlers.info_handler import InfoHandler
from src.utils import SessionManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# JSON-RPC Models
class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: Dict[str, Any] = {}
    id: Optional[Union[str, int]] = None

class JsonRpcResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[Union[str, int]] = None

class JsonRpcError(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None

# Rate limiting
request_counts = defaultdict(list)
RATE_LIMIT_REQUESTS = 100  # requests per window
RATE_LIMIT_WINDOW = 3600   # 1 hour in seconds

# Service instances
session_service = None
greptile_service = None
handlers = {}

def check_rate_limit(client_ip: str) -> bool:
    """Check if client has exceeded rate limit"""
    now = time.time()
    # Clean old requests
    request_counts[client_ip] = [
        req_time for req_time in request_counts[client_ip] 
        if now - req_time < RATE_LIMIT_WINDOW
    ]
    
    # Check limit
    if len(request_counts[client_ip]) >= RATE_LIMIT_REQUESTS:
        return False
    
    # Record this request
    request_counts[client_ip].append(now)
    return True

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup"""
    global session_service, greptile_service, handlers
    
    logger.info("🚀 Starting Greptile MCP HTTP server...")
    
    try:
        # Validate environment variables
        required_vars = ["GREPTILE_API_KEY", "GITHUB_TOKEN"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Initialize services (same as MCP version)
        session_manager = SessionManager()
        session_service = SessionService(session_manager)
        greptile_service = GreptileService(session_service)
        
        # Initialize handlers
        handlers = {
            'index_handler': IndexHandler(greptile_service),
            'query_handler': QueryHandler(greptile_service),
            'search_handler': SearchHandler(greptile_service),
            'info_handler': InfoHandler(greptile_service)
        }
        
        logger.info("✅ HTTP server initialized successfully")
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize HTTP server: {e}")
        raise
    finally:
        # Cleanup
        if greptile_service:
            await greptile_service.close_client()
        logger.info("🛑 HTTP server shutdown complete")

# FastAPI app with lifespan
app = FastAPI(
    title="Greptile MCP HTTP Gateway",
    description="HTTP/JSON-RPC interface for Greptile MCP tools",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

async def verify_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Verify API key if required"""
    # For now, API key verification is optional
    # In production, implement proper API key validation
    if credentials and credentials.credentials:
        # Add your API key validation logic here
        logger.info(f"API key provided: {credentials.credentials[:8]}...")
    return True

async def rate_limit_check(request: Request):
    """Check rate limiting"""
    client_ip = request.client.host
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=429, 
            detail="Rate limit exceeded. Please try again later."
        )
    return True

# JSON-RPC Error codes
class RpcErrorCodes:
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    RATE_LIMIT_EXCEEDED = -32001
    AUTHENTICATION_FAILED = -32002

async def handle_mcp_method(method: str, params: Dict[str, Any]) -> Any:
    """Route JSON-RPC methods to MCP handlers"""
    
    try:
        if method == "index_repository":
            required_params = ['remote', 'repository', 'branch']
            for param in required_params:
                if param not in params:
                    raise ValueError(f"Missing required parameter: {param}")
            
            return await handlers['index_handler'].handle_index_repository(
                remote=params['remote'],
                repository=params['repository'],
                branch=params['branch'],
                reload=params.get('reload', True),
                notify=params.get('notify', False)
            )
        
        elif method == "query_repository":
            required_params = ['query', 'repositories']
            for param in required_params:
                if param not in params:
                    raise ValueError(f"Missing required parameter: {param}")
            
            # Validate repositories format
            repositories = params['repositories']
            if not isinstance(repositories, list):
                raise ValueError("repositories must be a list")
            
            return await handlers['query_handler'].handle_query_repository(
                query=params['query'],
                repositories=json.dumps(repositories),
                session_id=params.get('session_id'),
                stream=params.get('stream', False),
                genius=params.get('genius', True),
                timeout=params.get('timeout'),
                messages=params.get('messages')
            )
        
        elif method == "search_repository":
            required_params = ['query', 'repositories']
            for param in required_params:
                if param not in params:
                    raise ValueError(f"Missing required parameter: {param}")
            
            repositories = params['repositories']
            if not isinstance(repositories, list):
                raise ValueError("repositories must be a list")
            
            return await handlers['search_handler'].handle_search_repository(
                query=params['query'],
                repositories=json.dumps(repositories),
                session_id=params.get('session_id'),
                genius=params.get('genius', True)
            )
        
        elif method == "get_repository_info":
            required_params = ['remote', 'repository', 'branch']
            for param in required_params:
                if param not in params:
                    raise ValueError(f"Missing required parameter: {param}")
            
            return await handlers['info_handler'].handle_get_repository_info(
                remote=params['remote'],
                repository=params['repository'],
                branch=params['branch']
            )
        
        elif method == "greptile_help":
            # Return help information
            return {
                "message": "Greptile MCP HTTP Gateway Help",
                "available_methods": [
                    "index_repository",
                    "query_repository", 
                    "search_repository",
                    "get_repository_info",
                    "greptile_help"
                ],
                "documentation": "/docs",
                "version": "1.0.0"
            }
        
        else:
            raise ValueError(f"Method '{method}' not found")
            
    except Exception as e:
        logger.error(f"Error handling method {method}: {str(e)}")
        raise

@app.post("/json-rpc", response_model=JsonRpcResponse)
async def handle_json_rpc(
    request: JsonRpcRequest,
    http_request: Request,
    _: bool = Depends(verify_api_key),
    __: bool = Depends(rate_limit_check)
) -> JsonRpcResponse:
    """Handle JSON-RPC 2.0 requests"""
    
    start_time = time.time()
    client_ip = http_request.client.host
    
    logger.info(f"📨 JSON-RPC request: {request.method} from {client_ip}")
    
    try:
        # Validate JSON-RPC format
        if request.jsonrpc != "2.0":
            return JsonRpcResponse(
                error=JsonRpcError(
                    code=RpcErrorCodes.INVALID_REQUEST,
                    message="Invalid JSON-RPC version. Must be '2.0'"
                ).__dict__,
                id=request.id
            )
        
        # Route to appropriate handler
        result = await handle_mcp_method(request.method, request.params)
        
        # Parse JSON result if string
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                pass  # Keep as string if not valid JSON
        
        response_time = time.time() - start_time
        logger.info(f"✅ JSON-RPC response: {request.method} completed in {response_time:.2f}s")
        
        return JsonRpcResponse(result=result, id=request.id)
        
    except ValueError as e:
        # Parameter validation errors
        logger.warning(f"⚠️ Parameter validation error: {str(e)}")
        return JsonRpcResponse(
            error=JsonRpcError(
                code=RpcErrorCodes.INVALID_PARAMS,
                message=f"Invalid parameters: {str(e)}"
            ).__dict__,
            id=request.id
        )
    
    except KeyError as e:
        # Missing method handler
        logger.warning(f"⚠️ Method not found: {str(e)}")
        return JsonRpcResponse(
            error=JsonRpcError(
                code=RpcErrorCodes.METHOD_NOT_FOUND,
                message=f"Method not found: {str(e)}"
            ).__dict__,
            id=request.id
        )
    
    except ValidationError as e:
        # Pydantic validation errors
        logger.warning(f"⚠️ Validation error: {str(e)}")
        return JsonRpcResponse(
            error=JsonRpcError(
                code=RpcErrorCodes.INVALID_PARAMS,
                message=f"Request validation failed: {str(e)}"
            ).__dict__,
            id=request.id
        )
    
    except Exception as e:
        # Internal server errors
        logger.error(f"❌ Internal error in {request.method}: {str(e)}")
        return JsonRpcResponse(
            error=JsonRpcError(
                code=RpcErrorCodes.INTERNAL_ERROR,
                message=f"Internal server error: {str(e)}"
            ).__dict__,
            id=request.id
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "greptile-mcp-http",
        "version": "1.0.0",
        "timestamp": time.time()
    }

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Greptile MCP HTTP Gateway",
        "version": "1.0.0",
        "description": "HTTP/JSON-RPC interface for Greptile MCP tools",
        "endpoints": {
            "json-rpc": "/json-rpc",
            "health": "/health",
            "docs": "/docs",
            "redoc": "/redoc"
        },
        "methods": [
            {
                "name": "index_repository",
                "description": "Index a repository for search and querying",
                "required_params": ["remote", "repository", "branch"]
            },
            {
                "name": "query_repository", 
                "description": "Query repositories with natural language",
                "required_params": ["query", "repositories"]
            },
            {
                "name": "search_repository",
                "description": "Search repositories for relevant files",
                "required_params": ["query", "repositories"]
            },
            {
                "name": "get_repository_info",
                "description": "Get information about an indexed repository",
                "required_params": ["remote", "repository", "branch"]
            },
            {
                "name": "greptile_help",
                "description": "Get help information about available methods",
                "required_params": []
            }
        ],
        "json_rpc_version": "2.0"
    }

@app.get("/api/methods")
async def list_methods():
    """List available JSON-RPC methods with documentation"""
    return {
        "methods": {
            "index_repository": {
                "description": "Index a repository for code search and querying",
                "parameters": {
                    "remote": {"type": "string", "description": "Repository platform (github/gitlab)", "required": True},
                    "repository": {"type": "string", "description": "Repository in owner/repo format", "required": True},
                    "branch": {"type": "string", "description": "Branch to index", "required": True},
                    "reload": {"type": "boolean", "description": "Force re-indexing", "default": True},
                    "notify": {"type": "boolean", "description": "Email notification on completion", "default": False}
                },
                "example": {
                    "jsonrpc": "2.0",
                    "method": "index_repository",
                    "params": {
                        "remote": "github",
                        "repository": "facebook/react",
                        "branch": "main"
                    },
                    "id": "1"
                }
            },
            "query_repository": {
                "description": "Query repositories with natural language",
                "parameters": {
                    "query": {"type": "string", "description": "Natural language query", "required": True},
                    "repositories": {"type": "array", "description": "List of repositories to query", "required": True},
                    "session_id": {"type": "string", "description": "Session ID for conversation continuity"},
                    "genius": {"type": "boolean", "description": "Use enhanced query mode", "default": True},
                    "stream": {"type": "boolean", "description": "Stream response", "default": False}
                },
                "example": {
                    "jsonrpc": "2.0",
                    "method": "query_repository",
                    "params": {
                        "query": "How does authentication work?",
                        "repositories": [
                            {"remote": "github", "repository": "facebook/react", "branch": "main"}
                        ]
                    },
                    "id": "2"
                }
            }
        }
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with JSON-RPC error format when appropriate"""
    if request.url.path == "/json-rpc":
        return JSONResponse(
            status_code=200,  # JSON-RPC errors use 200 with error in body
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": RpcErrorCodes.INTERNAL_ERROR,
                    "message": exc.detail
                },
                "id": None
            }
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
        log_level="info"
    )