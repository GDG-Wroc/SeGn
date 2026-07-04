from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware

from app.core.config import Config, config
from app.core.logger import setup_logging
from app.tools import register as register_tools


@dataclass
class AppContext:
    config: Config


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    setup_logging()
    yield AppContext(config=config)


mcp = FastMCP(
    "design-by-analogy-mcp",
    lifespan=lifespan,
    stateless_http=True,
    json_response=True,
)

register_tools(mcp)


if __name__ == "__main__":
    app = mcp.streamable_http_app()
    app = CORSMiddleware(
        app,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
        expose_headers=["Mcp-Session-Id"],
    )
    uvicorn.run(app, host=config.MCP_HOST, port=config.MCP_PORT)
