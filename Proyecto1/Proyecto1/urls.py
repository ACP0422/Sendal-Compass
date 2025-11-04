from django.contrib import admin
from django.urls import path, include
from principal import views
from django.conf import settings
from django.conf.urls.static import static

# ⬇️ Handlers de error (se usan cuando DEBUG=False)
from django.conf.urls import handler404, handler500


urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    # path('admin/', admin.site.urls),
    path("", views.index, name="index"),
    path("contacto/", views.contacto, name="contacto"),
    path("cotiza/", views.cotiza, name="cotiza"),
    # path("cotizador/", views.cotizador_index, name="cotizador"),
    # path("cotizador/<slug:slug>/", views.cotizador_detail, name="cotizador-detail"),
    # path('komchen-svg/', views.komchen_svg_view, name='komchen-svg'),
    # path('hacienda-svg/', views.hacienda_svg_view, name='hacienda-svg'),
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
    # path('proyectos/komchen/', views.komchen, name='komchen'),
    # path("api/", include("ghl_connector.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
handler400 = "principal.views.error_400"
handler403 = "principal.views.error_403"
handler404 = "principal.views.error_404"
handler500 = "principal.views.error_500"
