import os, re, json, requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .utils import get_access_token

GHL_API      = "https://services.leadconnectorhq.com"
LOCATION_ID  = os.getenv("GHL_LOCATION_ID")
API_VERSION  = os.getenv("GHL_API_VERSION", "2021-07-28")

CUSTOM_FIELDS = {
    "lot_id":          os.getenv("GHL_CF_LOT_ID"),
    "project":         os.getenv("GHL_CF_PROJECT"),
    "stage":           os.getenv("GHL_CF_STAGE"),
    "lot_status":      os.getenv("GHL_CF_LOT_STATUS"),
    "lot_area_m2":     os.getenv("GHL_CF_LOT_AREA_M2"),
    "lot_price_total": os.getenv("GHL_CF_LOT_PRICE"),
    "lot_price_m2":    os.getenv("GHL_CF_LOT_PRICE_M2"),
    "lot_image_url":   os.getenv("GHL_CF_LOT_IMAGE_URL"),
    "lot_dimensions":  os.getenv("GHL_CF_LOT_DIMENSIONS"),
    "down_payment_percent": os.getenv("GHL_CF_DOWN_PAYMENT_PERCENT"),
    "reservation_amount":  os.getenv("GHL_CF_RESERVATION_AMOUNT"),
    "deadline_days":       os.getenv("GHL_CF_DEADLINE_DAYS"),
    "financing_months":    os.getenv("GHL_CF_FINANCING_MONTHS"),
    "vs_entrega_percent":  os.getenv("GHL_CF_VS_ENTREGA_PERCENT"),
    "to_finance_percent":  os.getenv("GHL_CF_TO_FINANCE_PERCENT"),
    "price_per_stage":     os.getenv("GHL_CF_PRICE_PER_STAGE"),
}


LOT_ID_RE = re.compile(r"^MZ\d{2}-L\d{3}$", re.I)

def _headers():
    return {
        "Authorization": f"Bearer {get_access_token()}",
        "Accept": "application/json",
        "Version": API_VERSION,
    }

def _cf_list(payload_dict):
    """Convierte {'lot_id': 'MZ07-L021', ...} a la lista que espera GHL con IDs."""
    out = []
    for key, value in payload_dict.items():
        cf_id = CUSTOM_FIELDS.get(key)
        if cf_id and (value is not None and value != ""):
            # Algunas cuentas usan {"id": "...", "value": "..."} y otras {"customFieldId": "...", "value": "..."}.
            # La mayoría acepta "id".
            out.append({"id": cf_id, "value": value})
    return out

def _merge_tags(existing, to_add):
    base = set([t for t in (existing or []) if t])
    for t in to_add:
        if t:
            base.add(t)
    return list(base)

# =========================
# 1) Lead desde el mapa
# =========================
@csrf_exempt  # en prod mejor quitar y mandar X-CSRFToken desde el front
def create_lead(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    lot_id = (request.POST.get("lot_id") or "").strip()
    name   = (request.POST.get("name")   or "").strip()
    email  = (request.POST.get("email")  or "").strip()

    if not LOCATION_ID:
        return JsonResponse({"error": "Falta GHL_LOCATION_ID"}, status=500)
    if not lot_id:
        return JsonResponse({"error": "lot_id requerido"}, status=400)

    # Tags útiles para filtrar
    tags = ["Cotizador", "Sendal", f"lot:{lot_id}"]

    payload = {
        "locationId": LOCATION_ID,
        "name": f"Interés {lot_id}",  # nombre de la oportunidad
        # Si manejas contacto, aquí deberías pasar contactId (previo POST/GET a /contacts)
        "tags": tags,
        "customFields": _cf_list({
            "lot_id": lot_id,
            "lot_status": "interested"
        }),
    }

    try:
        r = requests.post(f"{GHL_API}/opportunities/", json=payload, headers=_headers(), timeout=20)
        data = r.json() if r.content else {}
        return JsonResponse(data, status=r.status_code)
    except requests.RequestException as e:
        return JsonResponse({"error": "network", "detail": str(e)}, status=502)

# =========================
# 2) Upsert de LOTES (admin)
# =========================
@csrf_exempt  # en prod mejor quitar y mandar X-CSRFToken desde el front
def lot_upsert(request):
    """
    Crea/actualiza una oportunidad 'lote' en GHL, con metadata:
    project, stage, lot_id, status, area_m2, price_total, image_url.
    Identifica el lote por tag 'lot:<ID>' y por custom field lot_id.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    if not LOCATION_ID:
        return JsonResponse({"error": "Falta GHL_LOCATION_ID"}, status=500)

    # --- recoge campos
    project     = (request.POST.get("project") or "").strip()   # "komchen" | "hacienda"
    stage       = (request.POST.get("stage")   or "").strip()   # "Etapa 1" o ""
    lot_id      = (request.POST.get("lot_id")  or "").strip()
    status      = (request.POST.get("status")  or "available").strip().lower()
    area_m2     = request.POST.get("area_m2")
    price_total = request.POST.get("price_total")
    image_url   = (request.POST.get("image_url") or "").strip()

    # --- validaciones básicas
    if not LOT_ID_RE.match(lot_id):
        return JsonResponse({"error": "lot_id inválido. Ej: MZ07-L021"}, status=400)
    if status not in ("available", "reserved", "sold"):
        return JsonResponse({"error": "status inválido"}, status=400)

    # normaliza números
    try:
        area_m2_f     = float(area_m2)     if area_m2     not in (None, "",) else None
        price_total_f = float(price_total) if price_total not in (None, "",) else None
    except ValueError:
        return JsonResponse({"error": "area_m2/price_total deben ser numéricos"}, status=400)

    # --- construye payload común
    cf_payload = {
        "lot_id":          lot_id,
        "project":         project,
        "stage":           stage or None,
        "lot_area_m2":     area_m2_f,
        "lot_price_total": price_total_f,
        "lot_image_url":   image_url or None,
        "lot_status":      status,
    }

    tags = [f"project:{project}", f"lot:{lot_id}"]
    if stage:
        tags.append(f"stage:{stage}")

    headers = _headers()

    # === Estrategia de upsert ===
    # 1) Opcional: intenta localizar una oportunidad del lote por el tag 'lot:<ID>'
    #    (Si tu cuenta tiene búsqueda por tags, úsala. Si no, puedes listar y filtrar)
    opp_id = None
    try:
        # Algunas cuentas exponen /opportunities/ con filtros; si no, omite este bloque.
        q = {"locationId": LOCATION_ID, "limit": 50}  # ajusta si tienes muchas
        resp = requests.get(f"{GHL_API}/opportunities/", params=q, headers=headers, timeout=20)
        if resp.ok:
            for o in (resp.json().get("opportunities") or resp.json().get("items") or []):
                otags = set([t.strip() for t in (o.get("tags") or [])])
                if f"lot:{lot_id}" in otags:
                    opp_id = o.get("id")
                    break
    except requests.RequestException:
        pass  # si falla la búsqueda, seguimos con create

    # 2) Si existe -> PATCH; si no -> POST (create)
    body = {
        "locationId": LOCATION_ID,
        "name": lot_id,            # nombre de la oportunidad = id del lote
        "status": status,          # usa tu propio mapeo de stages/pipelines si aplica
        "tags": tags,
        "customFields": _cf_list(cf_payload),
    }

    try:
        if opp_id:
            r = requests.patch(f"{GHL_API}/opportunities/{opp_id}", json=body, headers=headers, timeout=20)
        else:
            r = requests.post(f"{GHL_API}/opportunities/", json=body, headers=headers, timeout=20)

        data = r.json() if r.content else {}
        return JsonResponse(data, status=r.status_code)
    except requests.RequestException as e:
        return JsonResponse({"error": "network", "detail": str(e)}, status=502)
