from django.shortcuts import render, redirect
from django.templatetags.static import static
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.http import Http404

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
        "map_img": "resources/images/places/Hacienda/masterplan.png",
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
    otros = []
    for s in cfg.get("otros", []):
        other = COTIZADORES.get(s)
        if other:
            otros.append({"label": other["label"], "href": _href_to_detail(s), "btn": other["btn"]})
    grid_cols = min(3, max(1, len(otros)))
    title_color = cfg.get("title_color")
    title_style = f' style="color:{title_color}"' if title_color else ""
    ctx = {
        "page_title": cfg["title"],
        "hero_img": HERO_IMG, "kicker": KICKER, "heading": cfg["title"],
        "variant": cfg.get("variant"), "show_toggle": True,
        "actions": otros, "actions_hidden": True,
        "grid_cols": grid_cols,
        "map_img": cfg.get("map_img"),
        "title_style": title_style,
    }
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
            "activo": True,
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
                "map_url": "#",  # pon tu link de Google Maps
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
                # “Hotel” detrás del nombre en inglés => “Palacio Cantón Hotel”
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
