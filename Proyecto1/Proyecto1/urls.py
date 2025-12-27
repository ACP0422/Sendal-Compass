from django.contrib import admin
from django.urls import path, include
from principal import views
from django.conf import settings
from django.conf.urls.static import static
from django.views.i18n import JavaScriptCatalog  


# Handlers de error (se usan cuando DEBUG=False)


urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("", views.index, name="index"),
    path("contacto/", views.contacto, name="contacto"),
    path("cotiza/", views.cotiza, name="cotiza"),

 
    path("cotizador/", views.cotizador, name="cotizador"),
    path("cotizador-hacienda/", views.hacienda_svg_view, name="hacienda-svg"),

    path('api/lotes/', views.api_lotes, name='api_lotes'),
    path("api/lote/<str:lot_id>/", views.api_lote_detail, name="api-lote-detail"),
    path("api/cotiza-lote/", views.cotiza_lote, name="cotiza_lote"),


    path("proyectos/valladolid/", views.valladolid, name="valladolid"),
    path("proyectos/tulum/", views.tulum, name="tulum"),
    path("proyectos/valladolid/hacienda/", views.hacienda, name="hacienda"),
    path(
        "proyectos/valladolid/<slug:slug>/",
        views.predio_detail,
        name="predio-detail",
    ),
    path(
        "proyectos/valladolid/<slug:slug>/",
        views.predio_compat,
        name="valladolid-compat",
    ),
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
handler400 = "principal.views.error_400"
handler403 = "principal.views.error_403"
handler404 = "principal.views.error_404"
handler500 = "principal.views.error_500"
