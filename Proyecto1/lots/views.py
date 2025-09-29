from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, render
from .models import Development, Stage, Lot
from django.urls import reverse


def map_view(request, development_slug, stage_number):
    dev = get_object_or_404(Development, slug=development_slug)
    stage = get_object_or_404(Stage, development=dev, number=stage_number)
    return render(request, "lots/map.html", {
        "development_slug": development_slug,
        "stage_number": stage_number,
        "dev": dev,
        "stage": stage,
    })

def lots_json(request, development_slug, stage_number):
    dev = get_object_or_404(Development, slug=development_slug)
    stage = get_object_or_404(Stage, development=dev, number=stage_number)
    qs = stage.lots.order_by('code')  # <— clave: orden estable

    data = [{
        "svg_id": lot.svg_id,                # si lo tienes, se usará como id
        "code": lot.code,                    # ej. "1", "2", ... "9"
        
        "status": lot.status,                # "available" | "reserved" | "sold"
        "area_m2": float(lot.area_m2),
        "price": float(lot.list_price),
        "tooltip": lot.tooltip_label or f"Lote {lot.code} · {lot.area_m2} m²",
        "url": lot.get_absolute_url(),       # detalle
    } for lot in qs]
    return JsonResponse({"stage": stage.number, "lots": data})


def lot_detail(request, development_slug, stage_number, lot_code):
    dev = get_object_or_404(Development, slug=development_slug)
    stage = get_object_or_404(Stage, development=dev, number=stage_number)
    try:
        lot = stage.lots.get(code=lot_code)
    except Lot.DoesNotExist:
        raise Http404("Lote no encontrado")

    endpoint = reverse(
        "lots_json",
        kwargs={"development_slug": dev.slug, "stage_number": stage.number}
    )

    return render(
        request,
        "lots/lot_detail.html",
        {
            "dev": dev,
            "stage": stage,
            "lot": lot,
            "endpoint": endpoint,
        },
    )