from __future__ import annotations

import asyncio
import json

from mcp import Client

from server import mcp


async def main() -> None:
    print("=" * 60)
    print("MCP Job Postings Server – live tool calls")
    print("=" * 60)

    async with Client(mcp) as client:
        tools = await client.list_tools()
        print("\nAvailable tools:")
        for t in tools.tools:
            print(f"  • {t.name}: {t.description[:80]}...")

        print("\n--- search_postings_by_skill(skill='python', limit=3) ---")
        result = await client.call_tool(
            "search_postings_by_skill",
            {"skill": "python", "limit": 3},
        )
        print(json.dumps(result.structured_content, indent=2))

        print("\n--- count_postings_by_company(min_count=2) ---")
        result = await client.call_tool(
            "count_postings_by_company",
            {"min_count": 2},
        )
        print(json.dumps(result.structured_content, indent=2))

        print("\n--- get_posting(job_id='job-003') ---")
        result = await client.call_tool("get_posting", {"job_id": "job-003"})
        print(json.dumps(result.structured_content, indent=2))

        print("\n--- Validation: empty skill (should fail) ---")
        try:
            result = await client.call_tool(
                "search_postings_by_skill",
                {"skill": ""},
            )
            print("Unexpected success:", result)
        except Exception as e:
            print(f"Expected error: {type(e).__name__}: {e}")

        print("\n--- Validation: invalid job_id pattern (should fail) ---")
        try:
            result = await client.call_tool(
                "get_posting",
                {"job_id": "not-a-valid-id"},
            )
            if result.is_error:
                print("Tool error content:", result.content)
            else:
                print(json.dumps(result.structured_content, indent=2))
        except Exception as e:
            print(f"Expected error: {type(e).__name__}: {e}")

        print("\n--- Business error: unknown job_id ---")
        result = await client.call_tool("get_posting", {"job_id": "job-999"})
        if result.is_error:
            print("Tool error (as intended):")
            for block in result.content:
                print(f"  {block}")
        else:
            print(json.dumps(result.structured_content, indent=2))

    print("\n" + "=" * 60)
    print("All demonstrations finished successfully.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
