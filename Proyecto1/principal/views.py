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
from .forms import ContactForm, CotizaHomeForm, CotizaLoteForm
import logging
from django.core.mail import EmailMessage, BadHeaderError
from django.utils.translation import (
    gettext as __,
)
from django.utils.translation import gettext as __
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from pathlib import Path


import requests
import os




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

def cotizador(request):
    return redirect("hacienda-svg")


from django.views.decorators.http import require_GET
from django.core.cache import cache

from pathlib import Path



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
        "show_in_index": False,
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




def _proyectos():
    return [
        {
            "slug": None,
            "ubicacion": "valladolid",
            "nombre": "Valladolid",
            "url_name": "valladolid",
            "img": static("resources/images/places/Valladolid/Valladolid.jpg"),
            "descripcion": _(
                "Ciudad en crecimiento con alto potencial turístico e inmobiliario."
            ),
            "tipos": [],
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
            "tipos": ["tularum"],
            "activo": True,
        },
        {
            "slug": "hacienda",
            "ubicacion": "valladolid",
            "nombre": _("Hacienda Residencial Mayahuel"),
            "url_name": "predio-detail",
            "img": static("resources/images/places/Valladolid/hacienda/hero.jpg"),
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

    recipients = []
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
        messages.error(
            request, _("No hay destinatarios configurados para recibir la cotización.")
        )
        return render(request, "pages/index.html", _ctx_index(form), status=500)

    from_addr = getattr(settings, "DEFAULT_FROM_EMAIL", "") or getattr(
        settings, "EMAIL_HOST_USER", ""
    )
    if not from_addr:
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
            to=recipients,
            reply_to=[data["email"]],
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
                    from_email=from_email,
                    to=to_emails,
                    reply_to=[data["email"]],
                ).send(fail_silently=False)

            except BadHeaderError:
                messages.error(
                    request, _("Error al enviar el correo (cabecera inválida).")
                )
                return render(request, "pages/contacto.html", {"form": form})
            except Exception:
                messages.error(
                    request, _("No pudimos enviar tu mensaje. Inténtalo más tarde.")
                )
                return render(request, "pages/contacto.html", {"form": form})

            messages.success(request, _("¡Gracias! Recibimos tu mensaje."))
            return redirect("contacto")
        return render(request, "pages/contacto.html", {"form": form})

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
                "map_url": "https://www.google.com/maps?daddr=20.693193,-88.200813&saddr",
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
                "map_url": "https://www.google.com/maps/dir//20.68804,-88.199226/@21.0098422,-89.6157462,3653m/data=!3m1!1e3?entry=ttu&g_ep=EgoyMDI1MTEyMy4xIKXMDSoASAFQAw%3D%3D",
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



import re
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET




# ✅ 1) apunta al Excel real

LOT_RE = re.compile(r"^MZ(?P<mz>\d{2})-L(?P<lot>\d{1,3})$", re.I)

def normalize_lot_id(raw: str) -> str | None:
    """
    Acepta:
      MZ04-L2
      MZ04-L02
      MZ04-L002
    Devuelve SIEMPRE (UI):
      MZ04-L02  (2 dígitos)
    """
    if not raw:
        return None
    s = str(raw).strip().upper()
    m = LOT_RE.match(s)
    if not m:
        return None
    mz = int(m.group("mz"))
    lot = int(m.group("lot"))
    return f"MZ{mz:02d}-L{lot:02d}"






    

from django.views.decorators.http import require_GET
from django.http import JsonResponse
from principal.models import Lot
from .views import normalize_lot_id  # o utils.py si lo mueves

@require_GET
def api_lotes(request):
    qs = Lot.objects.all()

    payload = []
    for r in qs:
        lot_id = normalize_lot_id(r.id_lote) or (r.id_lote or "").strip().upper()

        payload.append({
            "id": lot_id,
            "code": lot_id,
            "id_lote": lot_id,

            "estado_lote": r.estado_lote,
            "precio_total": r.precio_total,
            "superficie_m2": r.superficie_m2,

            "precio_m2": r.precio_m2,
            "proyecto": r.proyecto,
            "manzana": r.manzana,
        })

    return JsonResponse({"results": payload, "items": payload, "lots": payload})

@require_GET
def api_lote_detail(request, lot_id: str):
    wanted = normalize_lot_id(lot_id)
    if not wanted:
        return JsonResponse({"error": "Lote no encontrado"}, status=404)

    lot = Lot.objects.filter(id_lote=wanted).first()
    if not lot:
        return JsonResponse({"error": "Lote no encontrado"}, status=404)

    d = {
        "id_lote": wanted,
        "estado_lote": lot.estado_lote,
        "precio_total": lot.precio_total,
        "precio_m2": lot.precio_m2,
        "superficie_m2": lot.superficie_m2,
        "proyecto": lot.proyecto,
        "manzana": lot.manzana,
        "medidas_lotes": lot.medidas_lotes,
        "cantidad_de_apartado": lot.cantidad_de_apartado,
        "dias_limite_apartado": lot.dias_limite_apartado,
        "cantidad_enganche": lot.cantidad_enganche,
        "cantidad_financiamiento": lot.cantidad_financiamiento,
        "pago_mensualidad": lot.pago_mensualidad,
        "cantidad_liquidacion": lot.cantidad_liquidacion,
        "url_imagen_lote": lot.url_imagen_lote,
    }
    return JsonResponse({"result": d})




from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.core.mail import BadHeaderError, EmailMessage
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _

import json
from django.shortcuts import render
from django.conf import settings
from pathlib import Path
from principal.models import Lot

def hacienda_svg_view(request):
    svg_path = Path(settings.BASE_DIR) / "static" / "maps" / "hacienda.svg"
    svg_markup = svg_path.read_text(encoding="utf-8")

    states = {}
    for lot in Lot.objects.only("id_lote", "estado_lote"):
        rid = normalize_lot_id(lot.id_lote)
        if not rid:
            continue

        s = (lot.estado_lote or "").lower()
        if "vend" in s:
            states[rid] = "sold"
        elif "apart" in s or "reserv" in s:
            states[rid] = "reserved"
        else:
            states[rid] = "available"

    return render(request, "hacienda.html", {
        "svg_markup": svg_markup,
        "lot_states_json": json.dumps(states, ensure_ascii=False),
    })




from django.views.decorators.http import require_POST

@require_POST
def cotiza_lote(request):
    form = CotizaLoteForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)

    data = form.cleaned_data

    subject = _("Solicitud de cotización — {lot} — {n} {a}").format(
        lot=data["id_lote"],
        n=data["nombre"],
        a=data["apellido"],
    )

    body = (
        f"Lote: {data['id_lote']}\n"
        f"Nombre: {data['nombre']} {data['apellido']}\n"
        f"Teléfono: {data['telefono']}\n"
        f"Email: {data['email']}\n"
    )

    to_emails = getattr(settings, "CONTACT_EMAILS", ["contacto@inmobiliariasendal.mx"])
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@inmobiliariasendal.mx")

    try:
        EmailMessage(
            subject=subject,
            body=body,
            from_email=from_email,
            to=to_emails,
            reply_to=[data["email"]],
        ).send(fail_silently=False)
    except Exception as e:
        logger.exception("Error enviando /cotiza-lote: %s", e)
        return JsonResponse(
            {"ok": False, "message": _("No pudimos enviar tu mensaje. Intenta más tarde.")},
            status=500,
        )

    return JsonResponse({"ok": True})
