"""
JSON-RPC 2.0 error codes and definitions.
"""


class RpcErrorCodes:
    """Standard JSON-RPC 2.0 error codes"""
    
    # Standard JSON-RPC 2.0 errors
    PARSE_ERROR = -32700       # Invalid JSON was received by the server
    INVALID_REQUEST = -32600   # The JSON sent is not a valid Request object
    METHOD_NOT_FOUND = -32601  # The method does not exist / is not available
    INVALID_PARAMS = -32602    # Invalid method parameter(s)
    INTERNAL_ERROR = -32603    # Internal JSON-RPC error
    
    # Custom application errors
    RATE_LIMIT_EXCEEDED = -32001      # Rate limit exceeded
    AUTHENTICATION_FAILED = -32002    # Authentication failed
    REPOSITORY_NOT_FOUND = -32003     # Repository not found
    INDEXING_FAILED = -32004          # Repository indexing failed
    QUERY_FAILED = -32005             # Query execution failed


class RpcErrors:
    """Predefined error messages"""
    
    @staticmethod
    def parse_error(details: str = "") -> dict:
        """Parse error response"""
        return {
            "code": RpcErrorCodes.PARSE_ERROR,
            "message": "Parse error",
            "data": details if details else None
        }
    
    @staticmethod
    def invalid_request(details: str = "") -> dict:
        """Invalid request error response"""
        return {
            "code": RpcErrorCodes.INVALID_REQUEST,
            "message": "Invalid Request",
            "data": details if details else None
        }
    
    @staticmethod
    def method_not_found(method_name: str = "") -> dict:
        """Method not found error response"""
        return {
            "code": RpcErrorCodes.METHOD_NOT_FOUND,
            "message": "Method not found",
            "data": f"Method '{method_name}' not found" if method_name else None
        }
    
    @staticmethod
    def invalid_params(details: str = "") -> dict:
        """Invalid parameters error response"""
        return {
            "code": RpcErrorCodes.INVALID_PARAMS,
            "message": "Invalid params",
            "data": details if details else None
        }
    
    @staticmethod
    def internal_error(details: str = "") -> dict:
        """Internal error response"""
        return {
            "code": RpcErrorCodes.INTERNAL_ERROR,
            "message": "Internal error",
            "data": details if details else None
        }
    
    @staticmethod
    def rate_limit_exceeded(details: str = "") -> dict:
        """Rate limit exceeded error response"""
        return {
            "code": RpcErrorCodes.RATE_LIMIT_EXCEEDED,
            "message": "Rate limit exceeded",
            "data": details if details else None
        }
    
    @staticmethod
    def authentication_failed(details: str = "") -> dict:
        """Authentication failed error response"""
        return {
            "code": RpcErrorCodes.AUTHENTICATION_FAILED,
            "message": "Authentication failed",
            "data": details if details else None
        }