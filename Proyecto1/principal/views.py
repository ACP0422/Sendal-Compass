from django.shortcuts import render, redirect
from django.templatetags.static import static
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.http import Http404
import json
from utils.lots_loader import load_states
from django.http import Http404
from django.shortcuts import render
from urllib.parse import urlparse, parse_qs
import re
from utils.lots_loader import load_inventory


import re
from urllib.parse import urlparse, parse_qs

def drive_urls(url: str) -> tuple[str | None, str | None]:
    """
    Recibe un vínculo de Drive y regresa:
      (primary_uc, fallback_lh3)
    - primary_uc  -> https://drive.google.com/uc?export=view&id=... [&resourcekey=...]
    - fallback_lh3-> https://lh3.googleusercontent.com/d/...
    Devuelve (None, None) si no parece de Drive.
    """
    if not url:
        return None, None

    p = urlparse(url)
    host = p.netloc
    if "drive.google.com" not in host and "docs.google.com" not in host:
        return None, None

    qs = parse_qs(p.query)
    file_id = None
    # /file/d/<ID>/...
    m = re.search(r"/file/d/([^/]+)", p.path)
    if m:
        file_id = m.group(1)
    # ?id=<ID>
    if not file_id and "id" in qs and qs["id"]:
        file_id = qs["id"][0]

    if not file_id:
        return None, None

    resourcekey = (qs.get("resourcekey") or [None])[0]

    primary = f"https://drive.google.com/uc?export=view&id={file_id}"
    if resourcekey:
        primary += f"&resourcekey={resourcekey}"

    fallback = f"https://lh3.googleusercontent.com/d/{file_id}"
    return primary, fallback




def lot_detail(request, slug: str, number: int):
    # si agregas ?reload=1 en la URL forzará releer el Excel
    force = request.GET.get("reload") == "1"
    inv_by_dev = load_inventory(force_reload=force)

    dev = inv_by_dev.get(slug, {}) or {}
    row = dev.get(number, {})  # dict con todas las columnas del Excel

    status = row.get("status", "disponible")
    area_m2 = float(row.get("area_m2") or 0)
    price_total = float(row.get("price_total") or 0)

    # Calcula precio/m2 si no viene en el archivo
    precio_m2 = float(row.get("precio_m2") or 0)
    if not precio_m2 and area_m2 > 0:
        precio_m2 = price_total / area_m2

    # Parámetros de etapa (administrables vía archivo)
    pct = float(row.get("stage_down_payment_percent") or 20.0)      # 20% por defecto
    apartar = float(row.get("stage_apartar_amount") or 1000.0)      # $1000 por defecto
    deadline_days = int(row.get("stage_deadline_days") or 5)        # 5 días por defecto

    # Enganche y saldo
    enganche_total = price_total * (pct / 100.0)
    saldo_enganche = max(enganche_total - apartar, 0.0)

    # Imagen dinámica (URL absoluta, Drive o estático) con fallback
    raw_img = (row.get("image_filename") or "").strip()
    image_url = ""
    image_url_fallback = ""

    if raw_img:
        if urlparse(raw_img).scheme in ("http", "https"):
            primary, fallback = drive_urls(raw_img)  # usa tu helper nuevo
            image_url = primary or raw_img
            image_url_fallback = fallback or ""
        else:
            image_url = f"STATIC::resources/images/lotes/{raw_img}"


    ctx = {
        "slug": slug,
        "number": number,
        "status": status,
        "area_m2": area_m2,

        # Datos para el popup (dinámicos)
        "precio_lista": price_total,
        "precio_m2": precio_m2,
        "enganche_total": enganche_total,
        "apartar_amount": apartar,
        "saldo_enganche": saldo_enganche,
        "deadline_days": deadline_days,
        "pct": pct,

        # Medidas
        "regular_width_m": row.get("regular_width_m"),
        "regular_length_m": row.get("regular_length_m"),
        "irregular_sides_m": row.get("irregular_sides_m"),

        # Imagen ya resuelta
        "image_url": image_url,
        "image_url_fallback": image_url_fallback,

    }

    partial = request.GET.get("partial") == "1" or request.headers.get("x-requested-with") == "XMLHttpRequest"
    tpl = "lots/_lot_detail_inner.html" if partial else "lots/lot_detail.html"
    return render(request, tpl, ctx)





def _enrich_hotspots_with_status(slug: str, hotspots: list[dict]) -> list[dict]:
    states_by_dev = load_states()                   # {'komchen': {9: 'vendido', ...}}
    states = states_by_dev.get(slug, {})
    out = []
    for h in hotspots:
        n = h.get("n")
        st = states.get(n, "disponible")           # default si no viene en Excel
        out.append({**h, "status": st})
    return out


# ===== Config global (cotizador) =====
HERO_IMG = "resources/images/cotizador/hero.png"
KICKER   = _("Cotiza nuestros proyectos")

COTIZADORES = {
    "komchen": {
        "label": _("Proyecto Komchén"),
        "title": _("Proyecto Komchén"),
        "variant": "komchen",
        "title_color": "#FCBB99",
        "map_img": "resources/images/places/Komchén/masterplan.png",
        "btn": "btn-komchen",
        "otros": ["hacienda"],
        "show_in_index": True,
    },
    "hacienda": {
        "label": _("Hacienda Residencial"),
        "title": _("Hacienda Residencial"),
        "variant": "hacienda",
        "title_color": "#F0C160",
        "map_img": "resources/images/places/Valladolid/hacienda/masterplan.png",
        "btn": "btn-hacienda",
        "otros": ["komchen"],
        "show_in_index": True,
    },
}
INDEX_ORDER = ["komchen", "hacienda"]

def _href_to_detail(slug: str) -> str:
    return reverse("cotizador-detail", args=[slug])

def cotizador_index(request):
    slugs = [s for s in INDEX_ORDER if COTIZADORES.get(s, {}).get("show_in_index")] \
            or [s for s, cfg in COTIZADORES.items() if cfg.get("show_in_index")]
    items = [{"label": COTIZADORES[s]["label"], "href": _href_to_detail(s), "btn": COTIZADORES[s]["btn"]}
             for s in slugs]
    grid_cols = min(3, max(1, len(items)))
    ctx = {
        "page_title": _("Cotizador"),
        "hero_img": HERO_IMG, "kicker": KICKER, "heading": _("Cotizador"),
        "variant": "", "show_toggle": False,
        "actions": items, "actions_hidden": False,
        "grid_cols": grid_cols,
        "map_img": None,
        "title_style": "",
    }
    return render(request, "pages/cotizador_base.html", ctx)



def cotizador_detail(request, slug: str):
    cfg = COTIZADORES.get(slug)
    if not cfg:
        return redirect("cotizador")

    # Construye la lista "otros"
    otros = []
    for s in cfg.get("otros", []):
        other = COTIZADORES.get(s)
        if other:
            otros.append({
                "label": other["label"],
                "href": _href_to_detail(s),
                "btn": other["btn"],
            })

    grid_cols = min(3, max(1, len(otros)))
    title_color = cfg.get("title_color")
    title_style = f' style="color:{title_color}"' if title_color else ""

    ctx = {
        "page_title": cfg["title"],
        "hero_img": HERO_IMG,
        "kicker": KICKER,
        "heading": cfg["title"],
        "variant": cfg.get("variant"),  # "komchen" | "hacienda"
        "show_toggle": True,
        "actions": otros,
        "actions_hidden": True,
        "grid_cols": grid_cols,
        "map_img": cfg.get("map_img"),
        "title_style": title_style,
        # genéricos para hotspots (se setean abajo según slug)
        "hotspots_json": None,
        "hotspot_label": None,
    }

    # ===== Hotspots por proyecto =====
    if slug == "komchen":
        komchen_hotspots = [
            {"n": 1, "x": 10.89, "y": 70.91},
            {"n": 2, "x": 13.13, "y": 90.43},
            {"n": 3, "x": 21.43, "y": 90.43},
            {"n": 4, "x": 26.34, "y": 90.63},
            {"n": 5, "x": 30.98, "y": 90.63},
            {"n": 6, "x": 35.54, "y": 90.23},
            {"n": 7, "x": 40.54, "y": 90.23},
            {"n": 8, "x": 45.27, "y": 90.23},
            {"n": 9, "x": 50.09, "y": 90.03},
            {"n":10, "x": 54.73, "y": 90.23},
            {"n":11, "x": 59.46, "y": 90.63},
            {"n":12, "x": 64.29, "y": 90.43},
            {"n":13, "x": 69.20, "y": 90.23},
            {"n":14, "x": 74.02, "y": 90.23},
            {"n":15, "x": 78.66, "y": 90.43},
            {"n":16, "x": 83.30, "y": 90.23},
            {"n":17, "x": 93.75, "y": 90.43},
            {"n":18, "x": 93.57, "y": 69.52},
            {"n":19, "x": 93.66, "y": 51.19},
            {"n":20, "x": 93.84, "y": 31.67},
            {"n":21, "x": 93.13, "y": 11.35},
            {"n":22, "x": 83.39, "y": 13.35},
            {"n":23, "x": 78.57, "y": 13.15},
            {"n":24, "x": 73.75, "y": 13.35},
            {"n":25, "x": 68.93, "y": 13.54},
            {"n":26, "x": 64.11, "y": 13.35},
            {"n":27, "x": 59.64, "y": 13.35},
            {"n":28, "x": 54.64, "y": 13.54},
            {"n":29, "x": 50.00, "y": 13.74},
            {"n":30, "x": 45.27, "y": 13.54},
            {"n":31, "x": 40.45, "y": 13.15},
            {"n":32, "x": 35.54, "y": 13.54},
            {"n":33, "x": 30.89, "y": 13.15},
            {"n":34, "x": 26.07, "y": 13.15},
            {"n":35, "x": 21.34, "y": 13.35},
            {"n":36, "x": 12.50, "y": 11.35},
            {"n":37, "x": 10.89, "y": 30.68},
        ]
        komchen_hotspots = _enrich_hotspots_with_status("komchen", komchen_hotspots)
        ctx["hotspots_json"] = json.dumps(komchen_hotspots)
        ctx["hotspot_label"] = _("Lote")

    elif slug == "hacienda":
        hacienda_hotspots = [
            {"n": 1, "x": 83.48, "y": 71.21},
            {"n": 2, "x": 75.63, "y": 70.97},
            {"n": 3, "x": 65.36, "y": 70.50},
            {"n": 4, "x": 55.63, "y": 66.21},
            {"n": 5, "x": 45.45, "y": 61.69},
            {"n": 6, "x": 35.54, "y": 60.73},
            {"n": 7, "x": 27.68, "y": 62.88},
        ]
        hacienda_hotspots = _enrich_hotspots_with_status("hacienda", hacienda_hotspots)
        ctx["hotspots_json"] = json.dumps(hacienda_hotspots)
        ctx["hotspot_label"] = _("Etapa")
    return render(request, "pages/cotizador_base.html", ctx)






# ===== Vistas públicas =====

def index(request):
    proyectos = [
        {
            "slug": "komchen",
            "nombre": "Komchén",
            "url": "komchen",
            "img": static("resources/images/places/Komchén/Komchén.png"),
            "descripcion": _("Zona con alta plusvalía y acceso rápido a la ciudad."),
            "tipos": ["otro"],
            "activo": True,
        },
        {
            "slug": "valladolid",
            "nombre": "Valladolid",
            "url": "valladolid",
            "img": static("resources/images/places/Valladolid/Valladolid.png"),
            "descripcion": _("Ciudad en crecimiento con alto potencial turístico e inmobiliario."),
            "tipos": ["lote", "otro"],
            "activo": True,
        },
        {
            "slug": "tulum",
            "nombre": "Tulum",
            "url": "tulum",
            "img": static("resources/images/places/Tulum/Tulum.jpg"),
            "descripcion": _("Destino icónico con gran plusvalía, naturaleza y proyección internacional."),
            "tipos": ["lote"],
            "activo": False,
        },
        
    ]
    return render(request, "pages/index.html", {"proyectos": proyectos})


def contacto(request):  return render(request, 'pages/contacto.html')
def valladolid(request): return render(request, 'pages/valladolid.html')
def tulum(request):       return render(request, 'pages/tulum.html')
def hacienda(request):    return render(request, 'pages/hacienda.html')
def komchen(request):     return render(request, 'pages/komchen.html')

# ===== Registro de predios =====
PREDIO_REGISTRY = {
    "hacienda": {
        "back_urlname": "hacienda",
        "municipio": _("Valladolid, Yucatán"),
        "predios": [
            {
                "slug": "predio1",
                "title": _("Predio 1"),
                "superficie_m2": 528,
                "hero": "resources/images/places/Valladolid/predio1/hero.png",
                "map_img": "resources/images/places/Valladolid/predio1/mapa.png",
                # ----- datos específicos -----
                "price_mxn": 2_904_000,
                "price_m2": 5500,
                "address": _("Calle 35 # 198 F"),
                "propiedad_tipo": _("Propiedad Privada"),
                "colonia": _("Centro"),
                "map_url": "#",  
                "features": [
                    _("Barda Perimetral"),
                    _("Puerta de Acceso"),
                    _("Uso de Suelo Comercial"),
                    _("A 2 calles de Catedral"),
                ],
                "subgallery": [
                    {"src": "resources/images/places/Valladolid/predio1/fachada.png",
                     "alt": _("Vista fachada"), "caption": _("Vista Fachada")},
                    {"src": "resources/images/places/Valladolid/predio1/satelite.png",
                     "alt": _("Vista satelital"), "caption": _("Vista Satelital")},
                ],
                
                "location_blurb": _(
                    "Ubicado en la C.35 a pocas calles del Hotel Palacio Cantón en Valladolid, Yucatán."
                ),
            },
            {
                "slug": "predio2",
                "title": _("Predio 2"),
                "superficie_m2": 520.65,
                "hero": "resources/images/places/Valladolid/predio2/fachada.png",
                "map_img": "resources/images/places/Valladolid/predio2/mapa.png",
                "price_mxn": 3_644_550,
                "price_m2": 7000,
                "address": _("Calle 39 #205 C"),
                "propiedad_tipo": _("Propiedad Privada"),
                "colonia": _("Centro"),
                "map_url": "#",
                "features": [
                    _("Construcción 321 m²"),
                    _("2 niveles"),
                    _("Barda Perimetral"),
                    _("Puerta de Acceso"),
                    _("Uso de Suelo Comercial"),
                    _("A 2 calles de Catedral"),
                ],
                "subgallery": [
                    {"src": "resources/images/places/Valladolid/predio2/fachada.png",
                     "alt": _("Vista fachada"), "caption": _("Vista Fachada")},
                    {"src": "resources/images/places/Valladolid/predio2/satelite.png",
                     "alt": _("Vista satelital"), "caption": _("Vista Satelital")},
                ],
                "location_blurb": _(
                    "Ubicado en la C.35 a pocas calles del Hotel Palacio Cantón en Valladolid, Yucatán."
                ),
            },
        ]
    }
}

def _find_predio(slug):
    for dev in PREDIO_REGISTRY.values():
        predios = dev["predios"]
        for i, p in enumerate(predios):
            if p["slug"] == slug:
                prev_p = predios[i - 1] if i > 0 else None
                next_p = predios[i + 1] if i < len(predios) - 1 else None
                return dev, p, prev_p, next_p
    return None, None, None, None

def predio_detail(request, slug):
    dev, p, prev_p, next_p = _find_predio(slug)
    if p is None:
        raise Http404("Predio no encontrado")

    # --- cadenas traducibles con variables ---
    price_text = None
    if p.get("price_mxn"):
        price_text = _("Precio: $%(amount)s MXN") % {"amount": f"{p['price_mxn']:,.0f}"}

    price_m2_str = None
    if p.get("price_m2"):
        price_m2_str = _("$%(amount)s m²") % {"amount": f"{p['price_m2']:,.0f}"}

    facts = [
        {"dt": p.get("address"), "dd": p.get("propiedad_tipo")},
        {"dt": price_m2_str, "dd": _("Precio por m²")},
        {"dt": _("Colonia:"), "dd": p.get("colonia")},
        {"dt": _("Municipio:"), "dd": _("Valladolid")},
    ]

    ctx = {
        "title": p["title"],
        "municipio": dev.get("municipio"),
        "superficie_m2": p.get("superficie_m2"),
        "hero_src": p.get("hero"),

        # navegación (nota: ahora el prev tiene prioridad en la plantilla)
        "back_urlname": dev.get("back_urlname"),
        "prev_slug": prev_p["slug"] if prev_p else None,
        "prev_label": prev_p["title"] if prev_p else None,
        "next_slug": next_p["slug"] if next_p else None,
        "next_label": next_p["title"] if next_p else None,

        # info
        "price_text": price_text,
        "facts": [f for f in facts if f["dt"] and f["dd"]],
        "features": p.get("features"),
        "map_url": p.get("map_url"),

        # subgalería y banda
        "subgallery": p.get("subgallery"),
        "band_theme": "band--gold",
        "location_blurb": p.get("location_blurb"),
        "map_img": p.get("map_img"),
        "map_iframe": None,  # si lo usas
    }
    return render(request, "pages/predio_base.html", ctx)


def predio_compat(request, slug):
    # /proyectos/valladolid/predio1/ -> redirige a la ruta nueva
    if slug.startswith("predio"):
        return redirect("predio-detail", slug=slug, permanent=True)
    raise Http404()
