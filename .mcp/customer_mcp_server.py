from mcp.server.fastmcp import FastMCP
from data.customers import (
    get_customer_list,
    get_customer_annual_spend,
    get_customer_office_locations
)

mcp = FastMCP("Customer MCP")

# @mcp.tool(
#     description="Get the annual spend made by a given customer."
# )
# def tool_get_customer_annual_spend(idx: int) -> int:
#     return get_customer_annual_spend(idx)

@mcp.tool(
    description="Get the list of country codes where a given customer has an office."
)
def tool_get_customer_office_locations(idx: int) -> list[str]:
    return get_customer_office_locations(idx)

@mcp.tool(
    description="Get the list of customers."
)
def tool_get_customer_list() -> list[dict]:
    return get_customer_list()

if __name__ == '__main__':
    mcp.run(transport="stdio")
