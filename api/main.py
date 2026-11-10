"""Local API scaffold backed exclusively by synthetic records."""

import json
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

app = FastAPI(title="Aegis Alumni Development API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["GET"],
    allow_headers=["Authorization"],
)
bearer = HTTPBearer(auto_error=False)
fixtures = Path(__file__).resolve().parents[1] / "fixtures"
records = json.loads((fixtures / "alumni.json").read_text(encoding="utf-8"))

# These public fixture tokens belong to the local mock only.
demo_clients = {
    "demo-campus-a": ("campus-a", {"alumni:read"}),
    "demo-campus-b": ("campus-b", {"alumni:read"}),
    "demo-proposals-only": ("campus-a", {"proposals:write"}),
}


class AlumniProfile(BaseModel):
    id: str
    name: str
    graduation_year: int
    employer: str
    title: str
    skills: list[str]


class AlumniPage(BaseModel):
    items: list[AlumniProfile]
    next_cursor: str | None = None


def read_tenant(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer)],
) -> str:
    client = demo_clients.get(credentials.credentials) if credentials else None
    if client is None:
        raise HTTPException(401, "Invalid development credential", {"WWW-Authenticate": "Bearer"})
    tenant, scopes = client
    if "alumni:read" not in scopes:
        raise HTTPException(403, "Missing alumni:read scope")
    return tenant


ReadTenant = Annotated[str, Depends(read_tenant)]
read_errors = {401: {"description": "Invalid credential"}, 403: {"description": "Missing scope"}}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/alumni", responses=read_errors)
def list_alumni(
    tenant: ReadTenant,
    q: Annotated[str, Query(max_length=100)] = "",
    graduation_year: Annotated[int | None, Query(ge=1900, le=2200)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: Annotated[str, Query(max_length=100)] = "",
) -> AlumniPage:
    query = q.strip().casefold()
    matching = []
    for record in sorted(records, key=lambda row: row["id"]):
        if record["tenant_id"] != tenant or record["id"] <= cursor:
            continue
        if graduation_year is not None and record["graduation_year"] != graduation_year:
            continue
        searchable = " ".join([record["name"], record["employer"], record["title"], *record["skills"]])
        if query in searchable.casefold():
            matching.append(AlumniProfile.model_validate(record))
    items = matching[:limit]
    return AlumniPage(items=items, next_cursor=items[-1].id if len(matching) > limit else None)


@app.get("/api/v1/alumni/{profile_id}", responses={**read_errors, 404: {"description": "Profile not found"}})
def get_alumni(profile_id: str, tenant: ReadTenant) -> AlumniProfile:
    for record in records:
        if record["tenant_id"] == tenant and record["id"] == profile_id:
            return AlumniProfile.model_validate(record)
    raise HTTPException(404, "Profile not found")
