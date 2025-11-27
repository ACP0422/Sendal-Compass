import requests
from django.conf import settings

import requests
from django.conf import settings


def _ghl_refresh_token() -> str | None:
    """
    Usa el REFRESH_TOKEN para obtener un nuevo ACCESS_TOKEN.
    Si el servidor rota el refresh, lo guardamos en settings en caliente.
    No persiste en disco (no cambia tu .env).
    """
    refresh_token = getattr(settings, "GHL_REFRESH_TOKEN", "")
    client_id = getattr(settings, "GHL_CLIENT_ID", "")
    client_secret = getattr(settings, "GHL_CLIENT_SECRET", "")
    api_base = settings.GHL_API_BASE.rstrip("/")

    if not (refresh_token and client_id and client_secret):
        return None  # no hay datos para refrescar

    url = f"{api_base}/oauth/token"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
    }
    r = requests.post(url, headers=headers, data=data, timeout=20)
    if r.status_code >= 400:
        return None

    payload = r.json()
    # Actualiza en caliente (memoria del proceso)
    if "access_token" in payload:
        settings.GHL_ACCESS_TOKEN = payload["access_token"]
    if "refresh_token" in payload and payload["refresh_token"]:
        settings.GHL_REFRESH_TOKEN = payload["refresh_token"]

    return getattr(settings, "GHL_ACCESS_TOKEN", None)


def _ghl_request(method: str, path: str, params=None, json=None, timeout=20):
    url = f"{settings.GHL_API_BASE.rstrip('/')}/{path.lstrip('/')}"
    headers = {
        "Accept": "application/json",
        "Version": settings.GHL_API_VERSION,
        "Authorization": f"Bearer {settings.GHL_ACCESS_TOKEN}",
    }

    # 1er intento con el token actual
    r = requests.request(
        method, url, headers=headers, params=params, json=json, timeout=timeout
    )

    # Si expira (401/403), refrescamos y reintentamos una sola vez
    if r.status_code in (401, 403):
        new_token = _ghl_refresh_token()
        if new_token:
            headers["Authorization"] = f"Bearer {new_token}"
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


# services.py NUEVO


def search_contact_by_email_or_phone(
    location_id: str, email: str | None = None, phone: str | None = None
):
    params = {"locationId": location_id}
    if email:
        params["query"] = email
    elif phone:
        params["query"] = phone

    status, data = _ghl_request("GET", "/contacts/search", params=params)
    if status != 200:
        return None

    contacts = data.get("contacts") or []
    return contacts[0] if contacts else None


def create_contact(
    location_id: str,
    first_name: str,
    last_name: str,
    email: str | None,
    phone: str | None,
):
    payload = {
        "locationId": location_id,
        "firstName": first_name,
        "lastName": last_name,
    }
    if email:
        payload["email"] = email
    if phone:
        payload["phone"] = phone

    status, data = _ghl_request("POST", "/contacts/", json=payload)

    # Caso normal: se creó el contacto
    if status in (200, 201):
        return data

    # Caso especial: la ubicación no permite duplicados y ya existe un contacto
    if (
        status == 400
        and isinstance(data, dict)
        and isinstance(data.get("meta"), dict)
        and data["meta"].get("contactId")
    ):
        contact_id = data["meta"]["contactId"]
        # Intentamos traer el contacto completo; si falla, devolvemos al menos el id
        _, contact_data = _ghl_request("GET", f"/contacts/{contact_id}")
        if isinstance(contact_data, dict):
            return contact_data
        return {"id": contact_id}

    # Cualquier otro error sí lo propagamos
    raise Exception(f"Error creando contacto: {status} {data}")


def get_or_create_contact(
    location_id: str,
    first_name: str,
    last_name: str,
    email: str | None,
    phone: str | None,
):
    # 1) Buscar primero
    contact = None
    if email:
        contact = search_contact_by_email_or_phone(location_id, email=email)
    if not contact and phone:
        contact = search_contact_by_email_or_phone(location_id, phone=phone)

    # 2) Crear si no existe
    if not contact:
        contact = create_contact(location_id, first_name, last_name, email, phone)

    return contact


def upsert_sales_opportunity(
    location_id: str,
    pipeline_id: str,
    pipeline_stage_id: str,
    contact_id: str,
    lot_data: dict,
    client_name: str,
):
    # Los campos del lote vienen de la oportunidad del pipeline Inventario
    # y sus valores están dentro de customFields (o customfields).
    cf = lot_data.get("customFields") or lot_data.get("customfields") or {}

    def val(key: str, cf_id: str | None = None, default=None):
        """
        Obtiene un valor del lote de la forma más robusta posible:

        1) lot_data[key] si existe.
        2) customFields:
           - si es dict: por id o por nombre.
           - si es lista: busca item con id/customFieldId == cf_id.
        """

        # 1) Top-level: lot_data["proyecto"], lot_data["manzana"], etc.
        if isinstance(lot_data, dict):
            v = lot_data.get(key)
            if v not in (None, "", []):
                return v

        # 2) customFields por id (cuando usamos los IDs de CF)
        if cf_id:
            # a) customFields como dict: {cf_id: valor} o {cf_id: {fieldValue: ...}}
            if isinstance(cf, dict):
                v = cf.get(cf_id)
                if isinstance(v, dict):
                    v = v.get("fieldValue") or v.get("value")
                if v not in (None, "", []):
                    return v

            # b) customFields como lista: [{"id": cf_id, "fieldValue": ...}, ...]
            if isinstance(cf, list):
                for item in cf:
                    if not isinstance(item, dict):
                        continue
                    if item.get("id") == cf_id or item.get("customFieldId") == cf_id:
                        v = item.get("fieldValue") or item.get("value")
                        if v not in (None, "", []):
                            return v

        # 3) customFields por nombre de campo (por si vienen como {"proyecto": "...", ...})
        if isinstance(cf, dict):
            v = cf.get(key)
            if v not in (None, "", []):
                return v

        return default


    # Identificadores importantes
    lot_id_val = val("lot_id", "WsuFeYWAl97hwKGYC5Vj", lot_data.get("name"))
    precio_total_val = val(
        "precio_total", "IETYqhhdidL1gXagEeMQ", lot_data.get("monetaryValue", 0)
    )

    body = {
        "locationId": location_id,
        "pipelineId": pipeline_id,
        "pipelineStageId": pipeline_stage_id,
        "contactId": contact_id,
        "name": f"Cotización {lot_id_val} – {client_name}",
        "status": "open",
        "monetaryValue": precio_total_val or 0,
        "customFields": [
            # Código / id de lote
            {
                "id": "WsuFeYWAl97hwKGYC5Vj",
                "fieldValue": val("lot_id", "WsuFeYWAl97hwKGYC5Vj", lot_id_val),
            },
            # Proyecto
            {
                "id": "MANmcJVjPiz0uBtCswUi",
                "fieldValue": val("proyecto", "MANmcJVjPiz0uBtCswUi"),
            },
            # Manzana
            {
                "id": "7d0qBsGivl3GT5qOUj1B",
                "fieldValue": val("manzana", "7d0qBsGivl3GT5qOUj1B"),
            },
            # Estado del lote
            {
                "id": "MwaBss3oDm6BKmD7QW0T",
                "fieldValue": val("estado_lote", "MwaBss3oDm6BKmD7QW0T"),
            },
            # Medidas básicas
            {
                "id": "IIqAas5DwSqRgEWFfhhT",
                "fieldValue": val("superficie_m2", "IIqAas5DwSqRgEWFfhhT"),
            },
            {
                "id": "88JKyJjACAbQiVdPnrF6",
                "fieldValue": val("precio_m2", "88JKyJjACAbQiVdPnrF6"),
            },
            {"id": "IETYqhhdidL1gXagEeMQ", "fieldValue": precio_total_val},
            # Enganche
            {
                "id": "X1kHLWMDpDaxfD9XV8RH",
                "fieldValue": val("porcentaje_enganche", "X1kHLWMDpDaxfD9XV8RH"),
            },
            {
                "id": "qO0hgq3VczuTDSJPZZbR",
                "fieldValue": val("cantidad_enganche", "qO0hgq3VczuTDSJPZZbR"),
            },
            # Financiamiento
            {
                "id": "r2z6j930QWIVPTCD5pcyn",
                "fieldValue": val("porcentaje_financiamiento", "r2z6j930QWIVPTCD5pcyn"),
            },
            {
                "id": "U76hbU22u2zGTfPsknznl",
                "fieldValue": val("cantidad_financiamiento", "U76hbU22u2zGTfPsknznl"),
            },
            {
                "id": "oIem9wTVBABQ4p8TSFFR",
                "fieldValue": val("meses_financiamiento", "oIem9wTVBABQ4p8TSFFR"),
            },
            {
                "id": "OgLkRRJU8dFATKWPJ2P3",
                "fieldValue": val("pago_mensualidad", "OgLkRRJU8dFATKWPJ2P3"),
            },
            # Liquidación
            {
                "id": "PMtcOa7frfBCo187VRvK",
                "fieldValue": val("porcentaje_liquidacion", "PMtcOa7frfBCo187VRvK"),
            },
            {
                "id": "XZqq60hdvHAPTKvJ2P3n",
                "fieldValue": val("cantidad_liquidacion", "XZqq60hdvHAPTKvJ2P3n"),
            },
            # Apartado
            {
                "id": "BKZKizfqsTaokY2v70iV",
                "fieldValue": val("cantidad_de_apartado", "BKZKizfqsTaokY2v70iV"),
            },
            {
                "id": "0EkDyVSOt4tD9o13PeeF",
                "fieldValue": val("dias_limite_apartado", "0EkDyVSOt4tD9o13PeeF"),
            },
            # Extras
            {
                "id": "3zfKmcTNjTscP1Y3KbLp",
                "fieldValue": val("medidas_lotes", "3zfKmcTNjTscP1Y3KbLp"),
            },
            {
                "id": "y3abg8Bi6bI93Mop4TxK",
                "fieldValue": val("url_imagen_lote", "y3abg8Bi6bI93Mop4TxK"),
            },
        ],
    }

    status, data = _ghl_request("POST", "/opportunities/upsert", json=body)
    if status not in (200, 201):
        raise Exception(f"Error upsert oportunidad ventas: {status} {data}")
    return data


def create_simple_opportunity(
    location_id: str,
    pipeline_id: str,
    pipeline_stage_id: str,
    contact_id: str,
    title: str,
    value: float | None = None,
    status: str = "open",
):
    """
    Crea una oportunidad sencilla en el pipeline de Ventas,
    sin datos de lote. Útil para formularios genéricos (home, contacto, etc.).
    """
    payload = {
        "locationId": location_id,
        "pipelineId": pipeline_id,
        "pipelineStageId": pipeline_stage_id,
        "contactId": contact_id,
        "name": title,
        "status": status,
    }
    if value is not None:
        payload["opportunityValue"] = value

    status_code, data = _ghl_request("POST", "/opportunities/", json=payload)

    if status_code not in (200, 201):
        raise Exception(f"Error creando oportunidad simple: {status_code} {data}")

    return data



def create_contact_note(contact_id: str, body: str):
    """
    Crea una nota en un contacto existente en GHL.
    Ruta:
        POST /contacts/{contact_id}/notes
    """
    url = f"{BASE_URL}/contacts/{contact_id}/notes"

    payload = {
        "body": body
    }

    resp = requests.post(
        url,
        json=payload,
        headers=get_headers()
    )

    if resp.status_code not in (200, 201):
        raise Exception(
            f"Error creando nota en contacto: {resp.status_code} {resp.text}"
        )

    return resp.json()

