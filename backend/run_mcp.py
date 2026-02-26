#!/usr/bin/env python3
"""Entry point for the Voss CRM MCP server.

Sets up sys.path and working directory so that `app.*` imports
and .env loading work correctly when spawned by Claude Desktop.
"""

import os
import sys

# Ensure the backend directory is on the Python path and is the cwd,
# so `app.config`, `app.sheets`, `app.services.*` all resolve correctly.
backend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(backend_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from mcp_server.server import mcp

if __name__ == "__main__":
    mcp.run(transport="stdio")
