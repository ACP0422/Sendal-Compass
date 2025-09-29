from django.contrib import admin
from django.urls import path, include
from principal import views

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('admin/', admin.site.urls),

    path('', views.index, name='index'),
    path('contacto/', views.contacto, name='contacto'),

    path("cotizador/", views.cotizador_index, name="cotizador"),
    path("cotizador/<slug:slug>/", views.cotizador_detail, name="cotizador-detail"),

    path('proyectos/valladolid/', views.valladolid, name='valladolid'),
    path('proyectos/tulum/', views.tulum, name='tulum'),
    path('proyectos/valladolid/hacienda/', views.hacienda, name='hacienda'),

    # predios (ruta correcta)
    path("proyectos/valladolid/predios/<slug:slug>/", views.predio_detail, name="predio-detail"),
    # compatibilidad /proyectos/valladolid/predio1/
    path("proyectos/valladolid/<slug:slug>/", views.predio_compat, name="valladolid-compat"),

    path('proyectos/komchen/', views.komchen, name='komchen'),

    path('hacienda/', include('lots.urls')),      
]