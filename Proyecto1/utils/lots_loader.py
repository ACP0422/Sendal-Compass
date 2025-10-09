from __future__ import annotations
import csv, io, urllib.request
from typing import Dict
from django.conf import settings

# Estados permitidos y normalización (acepta pequeños “typos”)
VALID = {"disponible", "vendido", "apartado"}
NORMALIZE = {
    "vendible": "vendido",    
    "vendido":  "vendido",
    "disponible": "disponible",
    "apartado":  "apartado",
}

_CACHE: Dict[str, Dict[int, str]] | None = None

def _fetch_bytes(url_or_path: str, timeout: int = 15) -> bytes:
    if url_or_path.startswith(("http://", "https://")):
        with urllib.request.urlopen(url_or_path, timeout=timeout) as r:
            return r.read()
    with open(url_or_path, "rb") as f:
        return f.read()

def _parse_csv(data: bytes) -> Dict[str, Dict[int, str]]:
    out: Dict[str, Dict[int, str]] = {}
    text = data.decode("utf-8-sig").splitlines()
    reader = csv.DictReader(text)
    for row in reader:
        dev = str(row.get("development", "")).strip().lower()
        num = str(row.get("number", "")).strip()
        st  = str(row.get("status", "")).strip().lower()
        st  = NORMALIZE.get(st, st)
        if not dev or st not in VALID:
            continue
        try:
            n = int(num)
        except:
            continue
        out.setdefault(dev, {})[n] = st
    return out

def _parse_xlsx(data: bytes) -> Dict[str, Dict[int, str]]:
    from openpyxl import load_workbook
    out: Dict[str, Dict[int, str]] = {}

    wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)

    # usa 'estados' si existe; si no, busca hoja con headers correctos
    ws = wb["estados"] if "estados" in wb.sheetnames else None
    if ws is None:
        for name in wb.sheetnames:
            _ws = wb[name]
            row1 = next(_ws.iter_rows(min_row=1, max_row=1, values_only=True), None)
            if not row1:
                continue
            header = [(str(c).strip().lower() if c is not None else "") for c in row1]
            if {"development", "number", "status"}.issubset(set(header)):
                ws = _ws
                break
    if ws is None:
        return out

    header_row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True), None)
    if not header_row:
        return out
    header = [(str(c).strip().lower() if c is not None else "") for c in header_row]
    need = ("development", "number", "status")
    if not set(need).issubset(set(header)):
        return out
    idx = {k: header.index(k) for k in need}

    for r in ws.iter_rows(min_row=2, values_only=True):
        if not r:
            continue
        dev = str(r[idx["development"]] if idx["development"] < len(r) else "").strip().lower()
        num_raw = r[idx["number"]] if idx["number"] < len(r) else ""
        st  = str(r[idx["status"]] if idx["status"] < len(r) else "").strip().lower()
        st  = NORMALIZE.get(st, st)
        if not dev or st not in VALID:
            continue
        try:
            n = int(str(num_raw).strip())
        except:
            continue
        out.setdefault(dev, {})[n] = st
    return out

def load_states(force_reload: bool = False) -> Dict[str, Dict[int, str]]:
    """Devuelve {development_slug: {lote_num: status}} a partir del Excel/CSV."""
    global _CACHE
    if _CACHE is not None and not force_reload:
        return _CACHE

    url = getattr(settings, "LOTS_SHEET_URL", "") or ""
    fmt = (getattr(settings, "LOTS_SHEET_FORMAT", "xlsx") or "xlsx").lower()
    timeout = int(getattr(settings, "LOTS_SHEET_TIMEOUT", 15))

    if not url:
        _CACHE = {}
        return _CACHE

    data = _fetch_bytes(url, timeout=timeout)
    _CACHE = _parse_csv(data) if fmt == "csv" else _parse_xlsx(data)
    return _CACHE
