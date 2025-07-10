"""
HTTP server entry point for Greptile MCP.
Provides JSON-RPC access to MCP tools via HTTP.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def validate_environment():
    """Validate required environment variables"""
    required_vars = ["GREPTILE_API_KEY", "GITHUB_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("\n📋 Required environment variables:")
        print("   GREPTILE_API_KEY - Your Greptile API key")
        print("   GITHUB_TOKEN - Your GitHub personal access token")
        print("\n💡 Set these in your .env file or environment")
        return False
    
    return True

def main():
    """Main entry point for HTTP server"""
    
    print("🚀 Greptile MCP HTTP Server")
    print("=" * 50)
    
    # Validate environment
    if not validate_environment():
        return 1
    
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    
    print(f"📡 Mode: HTTP/JSON-RPC Gateway")
    print(f"🌐 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"📚 Documentation: http://{host}:{port}/docs")
    print(f"🔍 API Methods: http://{host}:{port}/api/methods")
    print(f"❤️  Health Check: http://{host}:{port}/health")
    print("\n🎯 Starting server...")
    
    try:
        # Import uvicorn here to handle import errors gracefully
        import uvicorn
        
        # Start the server
        uvicorn.run(
            "src.http_server:app",
            host=host,
            port=port,
            reload=False,
            log_level="info",
            access_log=True
        )
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Install HTTP dependencies: pip install fastapi uvicorn")
        return 1
    except KeyboardInterrupt:
        print("\n⏹️  Server shutdown requested")
        return 0
    except Exception as e:
        print(f"❌ Server error: {e}")
        return 1

def run_dev():
    """Development server with auto-reload"""
    print("🔄 Development mode with auto-reload")
    
    if not validate_environment():
        return 1
    
    try:
        import uvicorn
        
        uvicorn.run(
            "src.http_server:app",
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8080")),
            reload=True,  # Enable auto-reload for development
            log_level="debug"
        )
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return 1
    except Exception as e:
        print(f"❌ Development server error: {e}")
        return 1

if __name__ == "__main__":
    # Check for development mode
    if len(sys.argv) > 1 and sys.argv[1] == "--dev":
        exit(run_dev())
    else:
        exit(main())