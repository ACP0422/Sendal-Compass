from django.shortcuts import render, redirect
from django.templatetags.static import static
from django.urls import reverse
from django.http import Http404
import json
from urllib.parse import urlparse, parse_qs
import re
from django.utils.translation import gettext as _
from django.utils.translation import pgettext
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from .forms import ContactForm, CotizaHomeForm
import logging
from django.core.mail import EmailMessage, BadHeaderError
from django.utils.translation import (
    gettext as __,
)
from django.utils.translation import gettext as __
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def render_error(request, code, title, message):
    ctx = {
        "code": code,
        "title": title,
        "message": message,
        "cta_text": _("Volver al inicio"),
        "cta_url": "index",
    }
    return render(request, "errors/error_base.html", ctx, status=code)


def error_404(request, exception):
    return render_error(
        request,
        404,
        _("Página no encontrada"),
        _("La página que estás buscando no existe o fue movida."),
    )


def error_500(request):
    return render_error(
        request,
        500,
        _("Error interno del servidor"),
        _("Ocurrió un problema inesperado. Estamos trabajando para solucionarlo."),
    )


def error_403(request, exception=None):
    return render_error(
        request,
        403,
        _("Acceso denegado"),
        _("No tienes permisos para acceder a este recurso."),
    )


def error_400(request, exception=None):
    return render_error(
        request,
        400,
        _("Solicitud inválida"),
        _("La petición no pudo procesarse. Verifica e inténtalo de nuevo."),
    )


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
    svg_urlname = SVG_ROUTES.get(slug)
    if not svg_urlname:
        raise Http404("Proyecto sin vista SVG configurada")
        # return redirect("cotizador")

    return redirect(svg_urlname)


@csrf_exempt
def create_lead(request):
    if request.method == "POST":
        data = json.loads(request.body)
        lot_id = data.get("lotId")
        source = data.get("source", "web")

        # Token de GHL (recuerda que expira cada día)
        token = "TU_ACCESS_TOKEN"

        # Endpoint de GHL (ejemplo: crear contacto)
        ghl_url = "https://services.leadconnectorhq.com/contacts/"

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
            "Content-Type": "application/json",
        }

        response = requests.post(ghl_url, headers=headers, json=payload)
        return JsonResponse(response.json(), safe=False)

    return JsonResponse({"error": "Invalid request"}, status=400)


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
KICKER = _("Cotiza nuestros proyectos")

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
    slugs = [s for s in INDEX_ORDER if COTIZADORES.get(s, {}).get("show_in_index")] or [
        s for s, cfg in COTIZADORES.items() if cfg.get("show_in_index")
    ]
    items = [
        {
            "label": COTIZADORES[s]["label"],
            "href": _href_to_detail(s),
            "btn": COTIZADORES[s]["btn"],
        }
        for s in slugs
    ]
    grid_cols = min(3, max(1, len(items)))
    ctx = {
        "page_title": _("Cotizador"),
        "hero_img": HERO_IMG,
        "kicker": KICKER,
        "heading": _("Cotizador"),
        "variant": "",
        "show_toggle": False,
        "actions": items,
        "actions_hidden": False,
        "grid_cols": grid_cols,
        "map_img": None,
        "title_style": "",
    }
    return render(request, "pages/cotizador_base.html", ctx)


logger = logging.getLogger(__name__)


def _proyectos():
    return [
        {
            "slug": None,
            "ubicacion": "valladolid",
            "nombre": "Valladolid",
            "url_name": "valladolid",
            "img": static("resources/images/places/Valladolid/Valladolid.png"),
            "descripcion": _(
                "Ciudad en crecimiento con alto potencial turístico e inmobiliario."
            ),
            "tipos": [],
            "activo": True,
        },
        {
            "slug": None,
            "ubicacion": "tulum",
            "nombre": _("Tularum"),
            "url_name": None,
            "external_url": "https://tularum.com",
            "img": static("resources/images/places/Tulum/tularum.png"),
            "descripcion": _(
                "Proyecto para invertir en extensiones de tierra en el codiciado Tulum en el estado de Quintana Roo, México."
            ),
            "tipos": ["tularum"],
            "activo": True,
        },
        {
            "slug": "predio",
            "ubicacion": "valladolid",
            "nombre": _("Predio Valladolid"),
            "url_name": "predio-detail",
            "img": static("resources/images/places/Valladolid/predio1/fachada.png"),
            "descripcion": _(
                "Ubicado en la C.35 a pocas calles del Hotel Palacio Cantón en Valladolid, Yucatán."
            ),
            "tipos": ["predios"],
            "activo": True,
        },
        {
            "slug": None,
            "ubicacion": "tulum",
            "nombre": "Tulum",
            "url_name": "tulum",
            "img": static("resources/images/places/Tulum/Tulum.jpg"),
            "descripcion": _(
                "Destino icónico con gran plusvalía, naturaleza y proyección internacional."
            ),
            "tipos": [],
            "activo": True,
        },
        {
            "slug": "hacienda",
            "ubicacion": "valladolid",
            "nombre": _("Hacienda Residencial Mayahuel"),
            "url_name": "predio-detail",
            "img": static("resources/images/places/Valladolid/hacienda/hero.png"),
            "descripcion": _(
                "Desarrollo residencial con fachada estilo hacienda y rodeado de paisajes de agave."
            ),
            "tipos": ["hacienda"],
            "activo": True,
        },
        {
            "slug": "casa-habitacion",
            "ubicacion": "valladolid",
            "nombre": _("Casa habitación Valladolid"),
            "url_name": "predio-detail",
            "img": static("resources/images/places/Valladolid/predio2/fachada.png"),
            "descripcion": _(
                "Ubicado en la C.35 a pocas calles del Hotel Palacio Cantón en Valladolid, Yucatán."
            ),
            "tipos": ["casa"],
            "activo": True,
        },
    ]


def _ctx_index(form=None):
    """
    Contexto base del index: proyectos + (form si se pasa).
    """
    ctx = {
        "proyectos": _proyectos(),
    }
    if form is not None:
        ctx["form"] = form
    return ctx


def index(request):
    """
    Home. Muestra los proyectos y el formulario de cotización.
    """
    # Si ya vienes de un POST de /cotiza con errores, el template recibirá "form".
    # Si no, renderizamos con form vacío.
    ctx = _ctx_index()
    ctx.setdefault("form", CotizaHomeForm())
    return render(request, "pages/index.html", ctx)


def cotiza(request):
    """
    Procesa el formulario del home.
    Siempre regresa a #cotiza (éxito o error), sin empujar el layout.
    """
    if request.method != "POST":
        return redirect(reverse("index") + "#cotiza")

    form = CotizaHomeForm(request.POST)
    if not form.is_valid():
        messages.error(request, _("Revisa los campos marcados."))
        return render(request, "pages/index.html", _ctx_index(form), status=400)

    data = form.cleaned_data

    # ----------------------------
    # Destinatarios y remitente seguros
    # ----------------------------
    recipients = []
    # Acepta cualquiera de tus keys de settings
    for name in ("CONTACT_EMAILS", "CONTACT_RECIPIENTS"):
        val = getattr(settings, name, None)
        if isinstance(val, (list, tuple)):
            recipients.extend([x for x in val if x])
        elif isinstance(val, str) and val:
            recipients.append(val)

    fallback = getattr(settings, "DEFAULT_FROM_EMAIL", "") or getattr(
        settings, "EMAIL_HOST_USER", ""
    )
    if not recipients and fallback:
        recipients = [fallback]

    if not recipients:
        # Evitamos 500 por mala configuración
        messages.error(
            request, _("No hay destinatarios configurados para recibir la cotización.")
        )
        return render(request, "pages/index.html", _ctx_index(form), status=500)

    from_addr = getattr(settings, "DEFAULT_FROM_EMAIL", "") or getattr(
        settings, "EMAIL_HOST_USER", ""
    )
    if not from_addr:
        # Último recurso: usa el primer destinatario
        from_addr = recipients[0]

    subject = _("Nueva solicitud de cotización — {n} {a}").format(
        n=data["nombre"], a=data["apellido"]
    )
    body = (
        f"Nombre: {data['nombre']} {data['apellido']}\n"
        f"Email: {data['email']}\n"
        f"Teléfono: {data['telefono']}\n"
        f"Tipo de propiedad: {data['tipo']}\n"
        f"Ubicación: {data['ubicacion']}\n"
    )

    try:
        msg = EmailMessage(
            subject=subject,
            body=body,
            from_email=from_addr,
            to=recipients,  # destinatarios
            reply_to=[data["email"]],  # así puedes responder al usuario
        )
        msg.send(fail_silently=False)
    except Exception as e:
        logger.exception("Error enviando /cotiza: %s", e)
        messages.error(request, _("No pudimos enviar tu mensaje. Intenta más tarde."))
        return render(request, "pages/index.html", _ctx_index(form), status=500)

    messages.success(request, _("¡Gracias! Nos pondremos en contacto contigo pronto."))
    return redirect(reverse("index") + "#cotiza")


def contacto(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            subject = _("Nueva solicitud de cotización — {n} {a}").format(
                n=data["nombre"], a=data["apellido"]
            )
            body = (
                f"Nombre: {data['nombre']} {data['apellido']}\n"
                f"Email: {data['email']}\n"
                f"Mensaje:\n{data.get('mensaje', '(sin mensaje)')}\n"
            )

            to_emails = getattr(
                settings, "CONTACT_EMAILS", ["contacto@inmobiliariasendal.mx"]
            )
            from_email = getattr(
                settings, "DEFAULT_FROM_EMAIL", "no-reply@inmobiliariasendal.mx"
            )

            try:
                EmailMessage(
                    subject=subject,
                    body=body,
                    from_email=from_email,  # remitente de tu dominio
                    to=to_emails,
                    reply_to=[data["email"]],  # responde directo al usuario
                ).send(fail_silently=False)

            except BadHeaderError:
                messages.error(
                    request, _("Error al enviar el correo (cabecera inválida).")
                )
                return render(request, "pages/contacto.html", {"form": form})
            except Exception:
                # No exponemos detalles técnicos al usuario
                messages.error(
                    request, _("No pudimos enviar tu mensaje. Inténtalo más tarde.")
                )
                return render(request, "pages/contacto.html", {"form": form})

            messages.success(request, _("¡Gracias! Recibimos tu mensaje."))
            return redirect("contacto")  # PRG: evita reenvío al refrescar
        # Form inválido: volvemos a pintar con errores de campo, sin mensaje global extra
        return render(request, "pages/contacto.html", {"form": form})

    # GET
    form = ContactForm()
    return render(request, "pages/contacto.html", {"form": form})


def valladolid(request):
    return render(request, "pages/valladolid.html")


def tulum(request):
    return render(request, "pages/tulum.html")


def hacienda(request):
    return render(request, "pages/hacienda.html")


def komchen(request):
    return render(request, "pages/komchen.html")


PREDIO_REGISTRY = {
    "hacienda": {
        "back_urlname": "hacienda",
        "municipio": _("Valladolid, Yucatán"),
        "predios": [
            {
                "slug": "predio",
                "title": _("Predio"),
                "superficie_m2": 528,
                "hero": "resources/images/places/Valladolid/predio1/hero.png",
                "map_img": "resources/images/places/Valladolid/predio1/mapa.png",
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
                    {
                        "src": "resources/images/places/Valladolid/predio1/fachada.png",
                        "alt": _("Vista fachada"),
                        "caption": _("Vista Fachada"),
                    },
                    {
                        "src": "resources/images/places/Valladolid/predio1/satelite.png",
                        "alt": _("Vista satelital"),
                        "caption": _("Vista Satelital"),
                    },
                ],
                "location_blurb": _(
                    "Ubicado en la C.35 a pocas calles del Hotel Palacio Cantón en Valladolid, Yucatán."
                ),
            },
            {
                "slug": "casa-habitacion",
                "title": _("Casa habitación"),
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
                    {
                        "src": "resources/images/places/Valladolid/predio2/fachada.png",
                        "alt": _("Vista fachada"),
                        "caption": _("Vista Fachada"),
                    },
                    {
                        "src": "resources/images/places/Valladolid/predio2/satelite.png",
                        "alt": _("Vista satelital"),
                        "caption": _("Vista Satelital"),
                    },
                ],
                "location_blurb": _(
                    "Ubicado en la C.35 a pocas calles del Hotel Palacio Cantón en Valladolid, Yucatán."
                ),
            },
        ],
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
        raise Http404(__("Predio no encontrado"))

    if p.get("price_mxn"):
        label_price = pgettext("price label", "Precio")
        amount = f"{p['price_mxn']:,.0f}"
        price_text = __("%(label)s: $%(amount)s %(currency)s") % {
            "label": label_price,
            "amount": amount,
            "currency": "MXN",
        }
    else:
        price_text = None

    if p.get("price_m2"):
        price_m2_str = __("$%(amount)s m²") % {"amount": f"{p['price_m2']:,.0f}"}
    else:
        price_m2_str = None

    facts = [
        {"dt": p.get("address"), "dd": p.get("propiedad_tipo")},
        {"dt": price_m2_str, "dd": __("Precio por m²")},
        {"dt": __("Colonia:"), "dd": p.get("colonia")},
        {"dt": __("Municipio:"), "dd": __("Valladolid")},
    ]
    facts = [f for f in facts if f["dt"] and f["dd"]]

    ctx = {
        "title": p["title"],
        "municipio": dev.get("municipio"),
        "superficie_m2": p.get("superficie_m2"),
        "hero_src": p.get("hero"),
        "back_urlname": dev.get("back_urlname"),
        "prev_slug": prev_p["slug"] if prev_p else None,
        "prev_label": prev_p["title"] if prev_p else None,
        "next_slug": next_p["slug"] if next_p else None,
        "next_label": next_p["title"] if next_p else None,
        "price_text": price_text,
        "facts": facts,
        "features": p.get("features"),
        "map_url": p.get("map_url"),
        "subgallery": p.get("subgallery"),
        "band_theme": "band--gold",
        "location_blurb": p.get("location_blurb"),
        "map_img": p.get("map_img"),
        "map_iframe": None,
    }

    if ctx.get("superficie_m2"):
        ctx["area_m2"] = ctx["superficie_m2"]

    return render(request, "pages/predio_base.html", ctx)


def predio_compat(request, slug):
    if slug.startswith("predio"):
        return redirect("predio-detail", slug=slug, permanent=True)
    raise Http404()
