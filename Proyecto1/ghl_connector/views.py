from django.http import JsonResponse
from django.conf import settings
from .services import search_opportunities  # seguimos usando tu helper principal
import requests


def _ghl_get_opportunity_detail(opportunity_id: str, timeout: int = 15):
    """
    Fallback ligero (no rompe nada): si la búsqueda no trae los valores
    de customFields, consultamos el detalle de la oportunidad para obtenerlos.
    """
    url = f"{settings.GHL_API_BASE.rstrip('/')}/opportunities/{opportunity_id}"
    headers = {
        "Accept": "application/json",
        "Version": settings.GHL_API_VERSION,
        "Authorization": f"Bearer {settings.GHL_ACCESS_TOKEN}",
    }
    r = requests.get(url, headers=headers, timeout=timeout)
    try:
        data = r.json()
    except Exception:
        data = {}
    # La API devuelve { "opportunity": {...} } en este endpoint
    return (r.status_code, (data.get("opportunity") or data))


def api_lots(request):
    limit = int(request.GET.get("limit", 50))
    code, data = search_opportunities(
        location_id=settings.GHL_LOCATION_ID,
        pipeline_id=settings.GHL_PIPELINE_INVENTARIO,
        pipeline_stage_id=settings.GHL_STAGE_INVENTARIO,
        status=request.GET.get("status", "open"),
        q=request.GET.get("q"),
        limit=limit,
        cursor=request.GET.get("cursor"),
    )
    if code != 200:
        return JsonResponse({"ok": False, "error": f"GHL {code}: {data}"}, status=code)

    # Algunos listados devuelven "items", otros "opportunities"
    raw_items = data.get("items") or data.get("opportunities") or []

    items = []
    for o in raw_items:
        # 1) Intentamos tomar los customFields de la búsqueda
        raw_cf = o.get("customFields") or o.get("customfields") or []

        fields: dict[str, object] = {}
        if isinstance(raw_cf, list):
            # Caso común en detalle: [{id, fieldValue}] – a veces la búsqueda ya trae esto
            for cf in raw_cf:
                fields[cf.get("id")] = cf.get("fieldValue") or cf.get("value")
        elif isinstance(raw_cf, dict):
            # A veces viene como dict de id->valor (pero suele venir en None)
            fields = dict(raw_cf)

        # 2) Si todo (o casi todo) vino en None, consultamos el detalle de la oportunidad
        needs_enrich = not fields or all(v in (None, "", []) for v in fields.values())
        if needs_enrich:
            d_code, detail = _ghl_get_opportunity_detail(o.get("id", ""))
            if d_code == 200 and isinstance(detail, dict):
                d_cf = detail.get("customFields") or []
                if isinstance(d_cf, list):
                    enriched = {
                        cf.get("id"): cf.get("fieldValue") or cf.get("value")
                        for cf in d_cf
                    }
                    # Solo sobrescribimos si hay algo útil
                    if any(v not in (None, "", []) for v in enriched.values()):
                        fields = enriched

        items.append(
            {
                "id": o.get("id"),
                "name": o.get("name"),
                "contactId": o.get("contactId"),
                "pipelineId": o.get("pipelineId"),
                "pipelineStageId": o.get("pipelineStageId"),
                "status": o.get("status"),
                "monetaryValue": o.get("monetaryValue"),
                "customFields": fields,  # <— ahora con valores cuando existan
            }
        )

    resp = {"ok": True, "count": len(items), "items": items}
    if "cursor" in data:
        resp["cursor"] = data["cursor"]
    return JsonResponse(resp)
