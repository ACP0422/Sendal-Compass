from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, render
from .models import Development, Stage, Lot

def map_view(request, development_slug, stage_number):
    dev = get_object_or_404(Development, slug=development_slug)
    stage = get_object_or_404(Stage, development=dev, number=stage_number)
    # Pasamos objetos y también los valores simples por comodidad
    return render(request, "lots/map.html", {
        "dev": dev,
        "stage": stage,
        "development_slug": dev.slug,
        "stage_number": stage.number,
    })

def lots_json(request, development_slug, stage_number):
    dev = get_object_or_404(Development, slug=development_slug)
    stage = get_object_or_404(Stage, development=dev, number=stage_number)
    qs = stage.lots.order_by('code')

    data = [{
        "svg_id": lot.svg_id or "",                    # autogenerado en save()
        "code": lot.code,
        "status": lot.status,                          # "available" | "reserved" | "sold"
        "area_m2": float(lot.area_m2 or 0),
        "price": float(lot.list_price or 0),
        "tooltip": lot.tooltip_label or f"Lote {lot.code}" + (f" · {lot.area_m2} m²" if lot.area_m2 else ""),
        "url": lot.get_absolute_url(),
    } for lot in qs]
    return JsonResponse({"stage": stage.number, "lots": data})


def lot_detail(request, development_slug, stage_number, lot_code):
    dev = get_object_or_404(Development, slug=development_slug)
    stage = get_object_or_404(Stage, development=dev, number=stage_number)
    try:
        lot = stage.lots.get(code=lot_code)
    except Lot.DoesNotExist:
        raise Http404("Lote no encontrado")
    return render(request, "lots/lot_detail.html", {"dev": dev, "stage": stage, "lot": lot})
