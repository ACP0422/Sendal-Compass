import requests
from django.conf import settings


def _ghl_request(method: str, path: str, params=None, json=None, timeout=20):
    url = f"{settings.GHL_API_BASE.rstrip('/')}/{path.lstrip('/')}"
    headers = {
        "Accept": "application/json",
        "Version": settings.GHL_API_VERSION,
        "Authorization": f"Bearer {settings.GHL_ACCESS_TOKEN}",
    }
    r = requests.request(
        method, url, headers=headers, params=params, json=json, timeout=timeout
    )
    try:
        data = r.json()
    except Exception:
        data = r.text
    return r.status_code, data


def search_opportunities(
    location_id: str,
    pipeline_id: str | None = None,
    pipeline_stage_id: str | None = None,
    status: str | None = "open",
    q: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
    include: str | None = None,  # <- NUEVO
):
    params = {"location_id": location_id, "limit": limit}
    if pipeline_id:
        params["pipeline_id"] = pipeline_id
    if pipeline_stage_id:
        params["pipeline_stage_id"] = pipeline_stage_id
    if status:
        params["status"] = status
    if q:
        params["q"] = q
    if cursor:
        params["cursor"] = cursor
    if include:  # <- NUEVO
        params["include"] = include  # <- NUEVO

    return _ghl_request("GET", "opportunities/search", params=params)


def get_opportunity(opportunity_id: str, include: str | None = "customFields"):
    params = {}
    if include:
        params["include"] = include
    return _ghl_request("GET", f"opportunities/{opportunity_id}", params=params)
