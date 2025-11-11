# ghl_connector/utils.py
from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional, Tuple
import requests
from django.conf import settings

# =========================
# Config / Constantes
# =========================

_API_BASE: str = getattr(
    settings, "GHL_API_BASE", "https://services.leadconnectorhq.com"
).rstrip("/")
_API_VER: str = getattr(settings, "GHL_API_VERSION", "2021-07-28")
_TIMEOUT: int = 15  # segundos

# Token “sub-account” vigente (el mismo que usas en Postman)
_ACCESS_TOKEN: str = getattr(settings, "GHL_ACCESS_TOKEN", "").strip()

# IDs que ya definiste en .env / settings
_LOCATION_ID: str = getattr(settings, "GHL_LOCATION_ID", "")
_PIPELINE_ID: str = getattr(settings, "GHL_PIPELINE_INVENTARIO", "")
_STAGE_ID: str = getattr(settings, "GHL_STAGE_INVENTARIO", "")

# Mapa de IDs de custom fields -> clave amigable
# (estos ids son los que usaste en Postman; si cambias alguno, actualiza aquí)
FIELD_ID_MAP: Dict[str, str] = {
    "WsuFeWAlA9TVhwKGYC5Vj": "id_lote",
    "MANmcJVjPiz0uBtCswUi": "proyecto",
    "7d0qBsGiV13GT5QgUj1B": "manzana",
    "MwaBss3oDm6BKmD70W0T": "estado_lote",
    "IIqAas5DwSqRgEWIFhHt": "superficie_m2",
    "88JKyJiACAb0iVdPnrF6": "precio_m2",
    "IETYqhhdiLdL9XagEeMQ": "precio_total",
    "X1kWLMDpDaxKfXW98RHV": "porcentaje_enganche",
    "BKKZiGfsTa0XKyZ70v7I": "cantidad_de_apartado",
    "0EkDyYSOt4t9oD3jPeef": "dias_limite_apartado",
    "iOme9wTVbAP4X8TpsFRF": "meses_financiamiento",
    "fz26j9UOZVT5CDrcgvn": "porcentaje_financiamiento",
    "Qq0HGq3WkVY1DPJjZZrB": "cantidad_enganche",
    "u76bHu22UvRPfdSzP0zn": "cantidad_financiamiento",
    "ogLKR8JUKvA4De0ee3TfD": "pago_mensualidad",
    "XZqq60dhvH4PRTKvJZP3": "porcentaje_liquidacion",
    "3zfKmcTNjTscP1Y3KbLp": "medidas_lotes",
    "y3abg8Bi6bI93Mop4TxK": "url_imagen_lote",
}

# =========================
# Helpers de HTTP
# =========================


def _api_url(path: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    return f"{_API_BASE}{path}"


def _headers(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    if not _ACCESS_TOKEN:
        # Evita llamadas sin token (devuelve un error consistente)
        return {
            "Accept": "application/json",
            "Version": _API_VER,
            "Authorization": "Bearer",  # vacío para provocar 401 controlado
        }
    base = {
        "Accept": "application/json",
        "Version": _API_VER,
        "Authorization": f"Bearer {_ACCESS_TOKEN}",
    }
    if extra:
        base.update(extra)
    return base


def _to_json(resp: requests.Response) -> Tuple[bool, Any]:
    try:
        data = resp.json()
    except Exception:
        data = resp.text
    ok = 200 <= resp.status_code < 300
    return ok, data


def ghl_get(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = _api_url(path)
    try:
        resp = requests.get(
            url, headers=_headers(), params=params or {}, timeout=_TIMEOUT
        )
    except requests.RequestException as e:
        return {"ok": False, "error": f"Network error: {e}"}
    ok, data = _to_json(resp)
    if not ok:
        return {"ok": False, "error": f"GHL {resp.status_code}: {data}"}
    return {"ok": True, "data": data}


def ghl_post(path: str, json_body: Dict[str, Any]) -> Dict[str, Any]:
    url = _api_url(path)
    try:
        resp = requests.post(
            url,
            headers=_headers({"Content-Type": "application/json"}),
            json=json_body,
            timeout=_TIMEOUT,
        )
    except requests.RequestException as e:
        return {"ok": False, "error": f"Network error: {e}"}
    ok, data = _to_json(resp)
    if not ok:
        return {"ok": False, "error": f"GHL {resp.status_code}: {data}"}
    return {"ok": True, "data": data}


# =========================
# Normalización de Oportunidades
# =========================


def _custom_fields_to_dict(raw_cf: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Convierte el arreglo de customFields de GHL a un dict {clave_amigable: valor}
    usando FIELD_ID_MAP. Ignora ids que no estén mapeados.
    """
    result: Dict[str, Any] = {}
    if not raw_cf:
        return result
    for item in raw_cf:
        fid = (item or {}).get("id")
        val = (item or {}).get("fieldValue")
        if fid in FIELD_ID_MAP:
            result[FIELD_ID_MAP[fid]] = val
    return result


def normalize_opportunity(op: Dict[str, Any]) -> Dict[str, Any]:
    """
    Estructura compacta y consistente para usar en tu front:
    """
    cf = _custom_fields_to_dict(op.get("customFields") or [])
    return {
        "id": op.get("id"),
        "name": op.get("name"),
        "contactId": op.get("contactId"),
        "pipelineId": op.get("pipelineId"),
        "pipelineStageId": op.get("pipelineStageId"),
        "status": op.get("status"),
        "monetaryValue": op.get("monetaryValue"),
        # Campos personalizados ya mapeados
        **cf,
    }


# =========================
# Funciones de Dominio (Inventario)
# =========================


def search_inventory_opportunities(
    *,
    location_id: Optional[str] = None,
    pipeline_id: Optional[str] = None,
    pipeline_stage_id: Optional[str] = None,
    status: str = "open",
    limit: int = 50,
) -> Dict[str, Any]:
    """
    GET /opportunities con filtros (según docs “Search Opportunity”).
    Usa query params: locationId, pipelineId, pipelineStageId, status, limit
    """
    loc = location_id or _LOCATION_ID
    pip = pipeline_id or _PIPELINE_ID
    stage = pipeline_stage_id or _STAGE_ID

    params = {
        "locationId": loc,
        "pipelineId": pip,
        "pipelineStageId": stage,
        "status": status,
        "limit": str(limit),
    }

    res = ghl_get("/opportunities", params=params)
    if not res.get("ok"):
        return res

    data = res["data"] or {}
    items = data.get("items") or []
    normalized = [normalize_opportunity(op) for op in items]
    return {"ok": True, "count": len(normalized), "items": normalized, "raw": data}


def get_opportunity(opportunity_id: str) -> Dict[str, Any]:
    """
    GET /opportunities/:id
    """
    if not opportunity_id:
        return {"ok": False, "error": "Missing opportunity_id"}
    res = ghl_get(f"/opportunities/{opportunity_id}")
    if not res.get("ok"):
        return res
    op = res["data"] or {}
    return {"ok": True, "item": normalize_opportunity(op), "raw": op}


# (Opcional) Variante POST /opportunities/search si quisieras usar ese endpoint:
def search_inventory_opportunities_post(
    *,
    location_id: Optional[str] = None,
    pipeline_id: Optional[str] = None,
    pipeline_stage_id: Optional[str] = None,
    status: str = "open",
    limit: int = 50,
    q: Optional[str] = None,
) -> Dict[str, Any]:
    """
    POST /opportunities/search
    Body JSON:
    {
      "locationId": "...", "pipelineId": "...", "pipelineStageId": "...",
      "status": "open", "limit": 50, "q": "texto"
    }
    """
    loc = location_id or _LOCATION_ID
    pip = pipeline_id or _PIPELINE_ID
    stage = pipeline_stage_id or _STAGE_ID

    body = {
        "locationId": loc,
        "pipelineId": pip,
        "pipelineStageId": stage,
        "status": status,
        "limit": limit,
    }
    if q:
        body["q"] = q

    res = ghl_post("/opportunities/search", json_body=body)
    if not res.get("ok"):
        return res

    data = res["data"] or {}
    items = data.get("items") or []
    normalized = [normalize_opportunity(op) for op in items]
    return {"ok": True, "count": len(normalized), "items": normalized, "raw": data}
