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

from pathlib import Path
import json
from django.conf import settings
from django.shortcuts import render
from utils.lots_loader import load_states  # fallback temporal a Excel


def _fetch_states_from_crm(dev_slug: str) -> dict[str, str]:
    """
    Devuelve { 'L-001': 'available'|'reserved'|'sold', ... } desde el CRM.
    Por ahora, hacemos fallback al Excel con tu util load_states().
    """
    try:
      states_by_dev = load_states(force_reload=False)  # {'komchen': {1:'disponible', ...}}
    except Exception:
      states_by_dev = {}

    raw = states_by_dev.get(dev_slug, {}) or {}  # {1:'vendido', ...}
    out: dict[str, str] = {}
    for num, st in raw.items():
        s = (st or "").lower()
        if "vend" in s: css = "sold"
        elif "apart" in s or "reserv" in s: css = "reserved"
        else: css = "available"
        out[f"L-{int(num):03d}"] = css
    return out

def komchen_svg_view(request):
    # 1) lee el SVG (guardado en static/maps/komchen.svg)
    svg_path = Path(settings.BASE_DIR) / 'static' / 'maps' / 'komchen.svg'
    svg_markup = svg_path.read_text(encoding='utf-8')

    # 2) estados (CRM → fallback Excel)
    lot_states = _fetch_states_from_crm('komchen')

    ctx = {
        'svg_markup': svg_markup,
        'lot_states_json': json.dumps(lot_states),
    }
    return render(request, 'komchen.html', ctx)



def hacienda_svg_view(request):
    
    svg_path = Path(settings.BASE_DIR) / 'static' / 'maps' / 'hacienda.svg'
    svg_markup = svg_path.read_text(encoding='utf-8')

    # 2) estados (CRM → fallback Excel)
    lot_states = _fetch_states_from_crm('hacienda')

    ctx = {
        'svg_markup': svg_markup,
        'lot_states_json': json.dumps(lot_states),
    }
    return render(request, 'hacienda.html', ctx)


from django.shortcuts import redirect
from django.http import Http404

# Si quieres ir sumando más proyectos SVG, mapea aquí: slug -> nombre_de_url
SVG_ROUTES = {
    "komchen": "komchen-svg",
    "hacienda": "hacienda-svg",   
}

def cotizador_detail(request, slug: str):
    """
    Vista del cotizador por proyecto.
    Ahora solamente redirige a la página SVG correspondiente.
    """
    # ¿tenemos ruta SVG para este proyecto?
    svg_urlname = SVG_ROUTES.get(slug)
    if not svg_urlname:
        # Si aún no existe el SVG de ese proyecto, puedes:
        # - mandar 404
        # - o redirigir al índice del cotizador
        raise Http404("Proyecto sin vista SVG configurada")
        # return redirect("cotizador")

    return redirect(svg_urlname)




import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def create_lead(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        lot_id = data.get('lotId')
        source = data.get('source', 'web')
        
        # Token de GHL (recuerda que expira cada día)
        token = 'TU_ACCESS_TOKEN'
        
        # Endpoint de GHL (ejemplo: crear contacto)
        ghl_url = 'https://services.leadconnectorhq.com/contacts/'

        payload = {
            "firstName": "Cotizador",        
            "lastName": f"Lote {lot_id}",
            "email": "contacto@sendal.mx",
            "phone": "9990000000",
            "customField": f"Lote seleccionado {lot_id}",
            "source": source,
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        response = requests.post(ghl_url, headers=headers, json=payload)
        return JsonResponse(response.json(), safe=False)

    return JsonResponse({'error': 'Invalid request'}, status=400)


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
            "activo": False,
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



# app/views.py
from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage, BadHeaderError
from django.shortcuts import render, redirect
from .forms import ContactForm

def contacto_view(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            # Honeypot: si viene lleno, asumimos bot y fingimos éxito
            if form.cleaned_data.get("website"):
                messages.success(request, "¡Gracias! Te contactaremos pronto.")
                return redirect("contacto")

            nombre   = form.cleaned_data["nombre"].strip()
            apellido = form.cleaned_data["apellido"].strip()
            email    = form.cleaned_data["email"].strip()
            mensaje  = form.cleaned_data.get("mensaje", "").strip()

            subject = f"[Sendal] Nuevo mensaje de contacto — {nombre} {apellido}"
            body = (
                f"Nombre: {nombre}\n"
                f"Apellido: {apellido}\n"
                f"Email: {email}\n\n"
                f"Mensaje:\n{mensaje or '(sin mensaje)'}"
            )

            to_list = getattr(settings, "CONTACT_RECIPIENTS", [settings.DEFAULT_FROM_EMAIL])
            email_msg = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=to_list,
                reply_to=[email] if email else None,
            )
            try:
                email_msg.send(fail_silently=False)
                messages.success(request, "¡Gracias! Tu mensaje fue enviado.")
                return redirect("contacto")
            except BadHeaderError:
                messages.error(request, "Encabezado de email inválido.")
            except Exception:
                messages.error(request, "Ocurrió un error al enviar tu mensaje. Inténtalo de nuevo.")
    else:
        form = ContactForm()

    return render(request, "contacto.html", {"form": form})












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
