# Proof the server works

## Method

Ran the in-memory client (`demo_client.py`) which uses the official `mcp.Client` against the live `MCPServer` instance. No network, no subprocess – pure protocol.

Command:

```bash
uv run python demo_client.py
```

## Output (abridged)

```
============================================================
MCP Job Postings Server – live tool calls
============================================================

Available tools:
  • search_postings_by_skill: Search the job-postings dataset for roles that list a given skill. ...
  • count_postings_by_company: Return how many job postings each company has in the dataset. ...
  • list_companies: Return the sorted list of unique company names present in the dataset.
  • get_posting: Fetch a single job posting by its stable ID. ...

--- search_postings_by_skill(skill='python', limit=3) ---
{
  "query_skill": "python",
  "total_matches": 6,
  "postings": [
    { "id": "job-003", "title": "Machine Learning Engineer", "company": "DataNova", ... },
    { "id": "job-001", "title": "Senior Python Engineer", "company": "Acme Corp", ... },
    { "id": "job-008", "title": "Security Engineer", "company": "SecureLayer", ... }
  ]
}

--- count_postings_by_company(min_count=2) ---
{
  "total_postings": 10,
  "companies": [
    { "company": "Acme Corp", "count": 3 },
    { "company": "CloudPath", "count": 3 },
    { "company": "DataNova", "count": 2 },
    { "company": "SecureLayer", "count": 2 }
  ]
}

--- get_posting(job_id='job-003') ---
{ "id": "job-003", "title": "Machine Learning Engineer", ... }

--- Validation: empty skill (should fail) ---
Error executing tool search_postings_by_skill: 1 validation error for search_postings_by_skillArguments
skill
  String should have at least 1 character [type=string_too_short, input_value='', input_type=str]

--- Validation: invalid job_id pattern (should fail) ---
Error executing tool get_posting: 1 validation error for get_postingArguments
job_id
  String should match pattern '^job-\\d{3}$' [type=string_pattern_mismatch, input_value='not-a-valid-id', input_type=str]

--- Business error: unknown job_id ---
Tool error (as intended): No job posting found with id='job-999'...
```

## How to reproduce with the MCP Inspector

```bash
uv run mcp dev server.py
```

Open the URL printed by the CLI, go to **Tools**, and call:

1. `search_postings_by_skill` with skill=`python`
2. `count_postings_by_company` with min_count=`1`
3. Intentionally submit an empty skill or a malformed `job_id` to see the validation messages.
