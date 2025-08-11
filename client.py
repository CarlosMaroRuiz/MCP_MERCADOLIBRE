import asyncio
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional

load_dotenv()
server = MCPServerStreamableHTTP('http://localhost:8000/mcp')
agent = Agent("google-gla:gemini-2.5-pro", toolsets=[server])

class ResultSearch(BaseModel):
    result_search: str
    error: Optional[str] = None
    num_iteration:int
    

async def main():
    async with agent:
        result = await agent.run('buscame una laptop gamer barata',output_type=ResultSearch)
    print(result.output)

if __name__ == "__main__":
    asyncio.run(main())