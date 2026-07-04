import asyncio
from fastmcp import Client

async def main():
    try:
        for host in ["http://localhost:8123/mcp", "http://127.0.0.1:8123/mcp"]:
            print(f"Connecting to {host}...")
            try:
                async with Client(host) as client:
                    tools = await client.list_tools()
                    print(f"Success! Tools: {[t.name for t in tools]}")
                    return
            except Exception as e:
                print(f"Failed: {e}")
    except Exception as e:
        print(f"Global error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
