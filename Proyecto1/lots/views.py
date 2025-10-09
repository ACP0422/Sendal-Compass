from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, render
from .models import Project, Lot

def lots_json(request, project_slug: str):
    """
    Devuelve el inventario del proyecto en JSON para tu SVG/JS.
    """
    project = get_object_or_404(Project, slug=project_slug)
    data = []
    qs = Lot.objects.filter(project=project).select_related("project")
    for lot in qs:
        data.append({
            "number": lot.number,
            "status": lot.status,
            "area_m2": float(lot.area_m2),
            "precio_lista": float(lot.precio_lista),
            "image_url": lot.display_image_url,  # puede ser None
        })
    return JsonResponse({"project": project.slug, "lots": data})

def lot_detail_modal(request, project_slug: str, number: int):
    lot = get_object_or_404(Lot, project__slug=project_slug, number=number)
    return render(request, "lots/lot_detail_modal.html", {
        "lot": lot,
        "number": lot.number,
        "area_m2": lot.area_m2,
        "status": lot.status,
        "updates": lot.payment_updates.all(),
    })
