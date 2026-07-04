from fastapi import HTTPException
import requests
import json
class MCP:

    def __init__(self, url:str = "http://localhost:8123/mcp"):
        self.mcp_uri=url

    def send_query_to_mcp(self, query: str):
    

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "search_parameter",
                "arguments": {
                    "query": query,
                    "limit": 5,
                },
            },
        }

        try:
            res = requests.post(
                self.mcp_uri,
                headers=headers,
                json=payload,
                timeout=10,
            )
            res.raise_for_status()

        except requests.RequestException as exc:
            raise HTTPException(
                status_code=502,
                detail=f"MCP request failed: {exc}",
            ) from exc

        content_type = res.headers.get("Content-Type", "")

        try:
            if "application/json" in content_type:
                return res.json()

            if "text/event-stream" in content_type:
                for line in res.text.splitlines():
                    if line.startswith("data:"):
                        data = line.removeprefix("data:").strip()
                        return json.loads(data)

                return {"response": res.text}

            return res.json()

        except ValueError:
            return {"response": res.text}