from __future__ import annotations

from typing import Annotated, Any

from pydantic import BaseModel, Field

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

JOB_POSTINGS: list[dict[str, Any]] = [
    {
        "id": "job-001",
        "title": "Senior Python Engineer",
        "company": "Acme Corp",
        "location": "San Francisco, CA",
        "skills": ["python", "fastapi", "postgresql", "docker"],
        "salary_min": 160000,
        "salary_max": 210000,
        "remote": True,
        "description": "Build high-performance APIs and data pipelines.",
    },
    {
        "id": "job-002",
        "title": "Frontend Developer",
        "company": "Acme Corp",
        "location": "Remote",
        "skills": ["typescript", "react", "css", "nextjs"],
        "salary_min": 130000,
        "salary_max": 170000,
        "remote": True,
        "description": "Ship polished UI for our customer dashboard.",
    },
    {
        "id": "job-003",
        "title": "Machine Learning Engineer",
        "company": "DataNova",
        "location": "New York, NY",
        "skills": ["python", "pytorch", "mlops", "kubernetes"],
        "salary_min": 175000,
        "salary_max": 230000,
        "remote": False,
        "description": "Train and deploy production ML models.",
    },
    {
        "id": "job-004",
        "title": "DevOps Engineer",
        "company": "CloudPath",
        "location": "Austin, TX",
        "skills": ["kubernetes", "terraform", "aws", "python"],
        "salary_min": 145000,
        "salary_max": 190000,
        "remote": True,
        "description": "Own CI/CD and infrastructure as code.",
    },
    {
        "id": "job-005",
        "title": "Full-Stack Engineer",
        "company": "DataNova",
        "location": "Remote",
        "skills": ["python", "react", "postgresql", "typescript"],
        "salary_min": 140000,
        "salary_max": 185000,
        "remote": True,
        "description": "Own features end-to-end across the stack.",
    },
    {
        "id": "job-006",
        "title": "Rust Systems Engineer",
        "company": "CloudPath",
        "location": "Seattle, WA",
        "skills": ["rust", "linux", "networking", "docker"],
        "salary_min": 170000,
        "salary_max": 220000,
        "remote": False,
        "description": "Build high-throughput networking components.",
    },
    {
        "id": "job-007",
        "title": "Data Engineer",
        "company": "Acme Corp",
        "location": "Chicago, IL",
        "skills": ["python", "spark", "sql", "airflow"],
        "salary_min": 150000,
        "salary_max": 195000,
        "remote": True,
        "description": "Design and operate large-scale data pipelines.",
    },
    {
        "id": "job-008",
        "title": "Security Engineer",
        "company": "SecureLayer",
        "location": "Remote",
        "skills": ["python", "go", "security", "aws"],
        "salary_min": 155000,
        "salary_max": 205000,
        "remote": True,
        "description": "Threat modeling and secure-by-default systems.",
    },
    {
        "id": "job-009",
        "title": "Platform Engineer",
        "company": "CloudPath",
        "location": "Remote",
        "skills": ["kubernetes", "go", "terraform", "prometheus"],
        "salary_min": 160000,
        "salary_max": 210000,
        "remote": True,
        "description": "Internal developer platform and observability.",
    },
    {
        "id": "job-010",
        "title": "Backend Engineer",
        "company": "SecureLayer",
        "location": "Boston, MA",
        "skills": ["go", "postgresql", "grpc", "docker"],
        "salary_min": 145000,
        "salary_max": 185000,
        "remote": False,
        "description": "Core services powering our security product.",
    },
]


class JobPostingSummary(BaseModel):
    id: str
    title: str
    company: str
    location: str
    skills: list[str]
    salary_min: int
    salary_max: int
    remote: bool


class SearchResult(BaseModel):
    query_skill: str
    total_matches: int
    postings: list[JobPostingSummary]


class CompanyCount(BaseModel):
    company: str
    count: int


class CountByCompanyResult(BaseModel):
    total_postings: int
    companies: list[CompanyCount]


mcp = MCPServer("Job Postings")


@mcp.tool(
    title="Search job postings by skill",
    annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False),
)
def search_postings_by_skill(
    skill: Annotated[
        str,
        Field(
            min_length=1,
            max_length=64,
            description="Skill to search for (case-insensitive). Examples: python, kubernetes, react.",
        ),
    ],
    limit: Annotated[
        int,
        Field(
            ge=1,
            le=50,
            description="Maximum number of matching postings to return.",
        ),
    ] = 10,
    remote_only: Annotated[
        bool,
        Field(description="If true, only return postings that allow remote work."),
    ] = False,
) -> SearchResult:
    """Search the job-postings dataset for roles that list a given skill.

    Matching is case-insensitive and looks for an exact skill token
    (e.g. 'python' matches the skill 'python', not 'pythonic').
    Results are ordered by highest max salary first.
    """
    skill_norm = skill.strip().lower()
    if not skill_norm:
        raise ValueError("skill must not be empty or whitespace-only")

    matches: list[dict[str, Any]] = []
    for job in JOB_POSTINGS:
        skills_lower = [s.lower() for s in job["skills"]]
        if skill_norm not in skills_lower:
            continue
        if remote_only and not job["remote"]:
            continue
        matches.append(job)

    matches.sort(key=lambda j: j["salary_max"], reverse=True)
    limited = matches[:limit]

    return SearchResult(
        query_skill=skill_norm,
        total_matches=len(matches),
        postings=[
            JobPostingSummary(
                id=j["id"],
                title=j["title"],
                company=j["company"],
                location=j["location"],
                skills=j["skills"],
                salary_min=j["salary_min"],
                salary_max=j["salary_max"],
                remote=j["remote"],
            )
            for j in limited
        ],
    )


@mcp.tool(
    title="Count postings by company",
    annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False),
)
def count_postings_by_company(
    min_count: Annotated[
        int,
        Field(
            ge=1,
            le=100,
            description="Only include companies that have at least this many postings.",
        ),
    ] = 1,
) -> CountByCompanyResult:
    """Return how many job postings each company has in the dataset.

    Companies are sorted by count descending, then by name.
    Use min_count to filter out companies with few openings.
    """
    counts: dict[str, int] = {}
    for job in JOB_POSTINGS:
        company = job["company"]
        counts[company] = counts.get(company, 0) + 1

    companies = [
        CompanyCount(company=name, count=cnt)
        for name, cnt in counts.items()
        if cnt >= min_count
    ]
    companies.sort(key=lambda c: (-c.count, c.company))

    return CountByCompanyResult(
        total_postings=len(JOB_POSTINGS),
        companies=companies,
    )


@mcp.tool(
    title="List companies",
    annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False),
)
def list_companies() -> list[str]:
    """Return the sorted list of unique company names present in the dataset."""
    return sorted({job["company"] for job in JOB_POSTINGS})


@mcp.tool(
    title="Get job posting by ID",
    annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False),
)
def get_posting(
    job_id: Annotated[
        str,
        Field(
            min_length=1,
            max_length=32,
            description="The job posting identifier, e.g. 'job-001'.",
            pattern=r"^job-\d{3}$",
        ),
    ],
) -> JobPostingSummary:
    """Fetch a single job posting by its stable ID.

    Raises a clear error if the ID does not exist so the model can recover.
    """
    for job in JOB_POSTINGS:
        if job["id"] == job_id:
            return JobPostingSummary(
                id=job["id"],
                title=job["title"],
                company=job["company"],
                location=job["location"],
                skills=job["skills"],
                salary_min=job["salary_min"],
                salary_max=job["salary_max"],
                remote=job["remote"],
            )
    raise ValueError(
        f"No job posting found with id={job_id!r}. "
        "Valid IDs look like 'job-001' through 'job-010'. "
        "Call list_companies or search_postings_by_skill first to discover IDs."
    )


if __name__ == "__main__":
    mcp.run()
