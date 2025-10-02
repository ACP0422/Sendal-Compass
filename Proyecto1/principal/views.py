from django.shortcuts import render, redirect
from django.templatetags.static import static
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.http import Http404
import json

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

    # Construye la lista "otros" (para el toggle)
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

    # Colorear título (opcional por config)
    title_color = cfg.get("title_color")
    title_style = f' style="color:{title_color}"' if title_color else ""

    # Contexto base
    ctx = {
        "page_title": cfg["title"],
        "hero_img": HERO_IMG,
        "kicker": KICKER,
        "heading": cfg["title"],
        "variant": cfg.get("variant"),
        "show_toggle": True,
        "actions": otros,
        "actions_hidden": True,
        "grid_cols": grid_cols,
        "map_img": cfg.get("map_img"),
        "title_style": title_style,
    }

    # ====== Komchén: hotspots por lote (x,y en %) ======
    if slug == "komchen":
        hotspots = [
            {"n": 1, "x": 10.89, "y": 70.91},
            {"n": 2, "x": 13.13, "y": 90.43},
            {"n": 3, "x": 21.43, "y": 90.43},
            {"n": 4, "x": 26.34, "y": 90.63},
            {"n": 5, "x": 30.98, "y": 90.63},
            {"n": 6, "x": 35.54, "y": 90.23},
            {"n": 7, "x": 40.54, "y": 90.23},
            {"n": 8, "x": 45.27, "y": 90.23},
            {"n": 9, "x": 50.09, "y": 90.03},
            {"n": 10, "x": 54.73, "y": 90.23},
            {"n": 11, "x": 59.46, "y": 90.63},
            {"n": 12, "x": 64.29, "y": 90.43},
            {"n": 13, "x": 69.20, "y": 90.23},
            {"n": 14, "x": 74.02, "y": 90.23},
            {"n": 15, "x": 78.66, "y": 90.43},
            {"n": 16, "x": 83.30, "y": 90.23},
            {"n": 17, "x": 93.75, "y": 90.43},
            {"n": 18, "x": 93.57, "y": 69.52},
            {"n": 19, "x": 93.66, "y": 51.19},
            {"n": 20, "x": 93.84, "y": 31.67},
            {"n": 21, "x": 93.13, "y": 11.35},
            {"n": 22, "x": 83.39, "y": 13.35},
            {"n": 23, "x": 78.57, "y": 13.15},
            {"n": 24, "x": 73.75, "y": 13.35},
            {"n": 25, "x": 68.93, "y": 13.54},
            {"n": 26, "x": 64.11, "y": 13.35},
            {"n": 27, "x": 59.64, "y": 13.35},
            {"n": 28, "x": 54.64, "y": 13.54},
            {"n": 29, "x": 50.00, "y": 13.74},
            {"n": 30, "x": 45.27, "y": 13.54},
            {"n": 31, "x": 40.45, "y": 13.15},
            {"n": 32, "x": 35.54, "y": 13.54},
            {"n": 33, "x": 30.89, "y": 13.15},
            {"n": 34, "x": 26.07, "y": 13.15},
            {"n": 35, "x": 21.34, "y": 13.35},
            {"n": 36, "x": 12.50, "y": 11.35},
            {"n": 37, "x": 10.89, "y": 30.68},
        ]
        ctx["komchen_hotspots_json"] = json.dumps(hotspots) 

    # ====== Hacienda: integra el mapa interactivo de lots ======
    if slug == "hacienda":
        dev_slug = "hacienda-residencial"  # Debe coincidir con Development.slug en DB
        stage_number = 1

        ctx["show_lots_map"] = True
        ctx["lots_dev_slug"] = dev_slug
        ctx["lots_stage_number"] = stage_number

        # URL del JSON ya resuelta (evita armarla en plantilla)
        ctx["lots_endpoint"] = reverse(
            "lots_json",
            kwargs={"development_slug": dev_slug, "stage_number": stage_number},
        )

        # Si quisieras ocultar la imagen estática del masterplan y mostrar solo el SVG/JS:
        # ctx["map_img"] = None

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
