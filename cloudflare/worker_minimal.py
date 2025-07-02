"""
Minimal Cloudflare Workers Python entry point for testing.
"""

async def on_fetch(request):
    """Minimal test worker."""
    from js import Response, Headers, JSON
    
    # Simple response
    response_data = {
        "status": "working",
        "message": "Minimal worker is responding"
    }
    
    headers = Headers.new()
    headers.set("Content-Type", "application/json")
    headers.set("Access-Control-Allow-Origin", "*")
    
    return Response.new(
        JSON.stringify(response_data),
        status=200,
        headers=headers
    )

# Export for Cloudflare Workers
export = {"fetch": on_fetch}