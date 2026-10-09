# MCP Job Postings Server

A small [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server built with the official Python SDK (`mcp`). It exposes tools over a sample dataset of tech job postings so an AI assistant can search and aggregate openings.

## Tools

| Tool | Description |
|------|-------------|
| `search_postings_by_skill` | Find postings that list a given skill (case-insensitive). Supports `limit` and `remote_only`. |
| `count_postings_by_company` | Count postings per company; optional `min_count` filter. |
| `list_companies` | Sorted list of unique company names. |
| `get_posting` | Fetch one posting by ID (`job-001` … `job-010`). |

All tools declare **typed inputs** (Pydantic / type hints), rich **Field descriptions**, and numeric/string constraints. Invalid arguments are rejected *before* the tool body runs, with clear Pydantic validation messages the model can use to self-correct.

## Quick start

### Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Install & run (stdio – default)

```bash
uv sync
uv run python server.py
# or: uv run mcp run server.py
```

### Interactive exploration (MCP Inspector)

```bash
uv run mcp dev server.py
```

This launches the [MCP Inspector](https://github.com/modelcontextprotocol/inspector). Open the printed URL, switch to the **Tools** tab, and call any tool. The form fields and validation are generated from the type hints.

### Programmatic demo

```bash
uv run python demo_client.py
```

The script uses an in-memory `Client(mcp)` (no subprocess, no network) and exercises happy paths plus validation / business errors.

### HTTP transport (stretch)

```bash
uv run python -c "
from server import mcp
mcp.run(transport='streamable-http', port=8000)
"
# Clients connect to http://127.0.0.1:8000/mcp
```

## Dataset

Ten synthetic postings across four companies (Acme Corp, DataNova, CloudPath, SecureLayer). Skills include python, rust, go, kubernetes, react, etc. Salaries and remote flags are included for richer filtering demos.

## Input validation examples

| Call | Result |
|------|--------|
| `skill=""` | Pydantic: *String should have at least 1 character* |
| `job_id="not-a-valid-id"` | Pydantic: *String should match pattern '^job-\\d{3}$'* |
| `limit=999` | Pydantic: *Input should be less than or equal to 50* |
| `job_id="job-999"` | Tool error: *No job posting found with id='job-999'…* |

## Protecting the server with OAuth 2.0

When the server is exposed over **Streamable HTTP** (or SSE), it becomes an ordinary web resource server and should be protected with OAuth 2.1 bearer tokens. The MCP Python SDK already ships the building blocks.

### Recommended flow

Use the **Authorization Code flow with PKCE** (OAuth 2.1). This is the only flow suitable for public clients (desktop apps, browser-based hosts, Claude Desktop, Cursor, etc.):

1. The MCP **client** discovers the authorization server via the resource server’s **Protected Resource Metadata** (RFC 9728) at `/.well-known/oauth-protected-resource`.
2. The client performs dynamic client registration (if needed) and redirects the user to the authorization server’s `/authorize` endpoint with a PKCE `code_challenge`.
3. After user consent the authorization server redirects back with an authorization code.
4. The client exchanges the code + `code_verifier` at the token endpoint and receives an access token (and optionally a refresh token).
5. Every subsequent MCP request carries `Authorization: Bearer <access_token>`.

For machine-to-machine / backend clients the **Client Credentials** grant can be used instead, but interactive AI hosts should stick to Authorization Code + PKCE.

### Where tokens are checked

- On **every** HTTP request that hits the MCP endpoint (`/mcp`).
- The SDK’s HTTP transport extracts the bearer token and hands it to a `TokenVerifier` implementation you provide.
- Verification happens *before* any tool, resource or prompt handler runs. A missing or invalid token yields `401 Unauthorized` (with a `WWW-Authenticate` header pointing at the authorization server).

Typical `TokenVerifier` responsibilities:

- Validate signature / encryption (JWT) or introspect the token against the authorization server.
- Check `exp`, `nbf`, `iss`, and (when `validate_token_resource=True`) that the token’s audience / resource matches this server.
- Enforce the required scopes (see below).
- Return an `AccessToken` object (subject, scopes, expiry) or `None` to reject.

### Scopes we would define

Keep scopes coarse and aligned with the data surface:

| Scope | Meaning |
|-------|---------|
| `jobs:read` | Call any of the read-only tools (`search_postings_by_skill`, `count_postings_by_company`, `list_companies`, `get_posting`). |
| `jobs:admin` | Future write tools (create / update / delete postings) – not implemented yet. |

In `AuthSettings` you would set:

```python
from pydantic import AnyHttpUrl
from mcp.server import MCPServer
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings

class MyTokenVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        # Validate JWT / call introspection endpoint …
        # Return AccessToken(token=token, client_id=…, scopes=[…], expires_at=…)
        # or None to reject.
        ...

mcp = MCPServer(
    "Job Postings",
    token_verifier=MyTokenVerifier(),
    auth=AuthSettings(
        issuer_url=AnyHttpUrl("https://auth.example.com"),
        resource_server_url=AnyHttpUrl("https://jobs.example.com/mcp"),
        required_scopes=["jobs:read"],
        validate_token_resource=True,
    ),
)
```

Because every tool in this server is read-only, a single `jobs:read` scope is sufficient for the current surface. Adding a mutation tool later would simply require the tighter `jobs:admin` scope (checked inside the tool or via a second `required_scopes` policy).

### Summary

| Concern | Choice |
|---------|--------|
| Flow | Authorization Code + PKCE (public clients) |
| Token check location | Every HTTP request, inside the transport / `TokenVerifier` |
| Scopes | `jobs:read` (current tools), `jobs:admin` (future writes) |
| Metadata | RFC 9728 Protected Resource Metadata + OAuth AS metadata |

See the SDK docs on [Authorization](https://py.sdk.modelcontextprotocol.io/run/authorization/) and the `examples/servers/simple-auth` sample for a full Authorization-Server + Resource-Server pair.

## Project layout

```
server.py          # MCPServer + tools + sample data
demo_client.py     # In-memory client that exercises the tools
README.md          # This file
pyproject.toml     # Dependencies (mcp[cli])
```

## License

MIT
