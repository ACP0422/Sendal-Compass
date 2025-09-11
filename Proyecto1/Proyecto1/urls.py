"""
URL configuration for Proyecto1 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from principal import views


urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),  # necesario para set_language
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),  
    path('contacto/', views.contacto, name='contacto'),
    path('cotizador/', views.cotizador, name='cotizador'),
    path('cotizador/cotizador-komchen', views.cotizadorKomchen, name='cotizador-komchen'),
    path('proyectos/valladolid/', views.valladolid, name='valladolid'),
    path('proyectos/tulum/', views.tulum, name='tulum'), 
    path('proyectos/valladolid/hacienda/', views.hacienda, name='hacienda'),
    path('proyectos/valladolid/predio1/', views.predio1, name='predio1'),
    path('proyectos/valladolid/predio2/', views.predio2, name='predio2'),
    path('proyectos/komchen/', views.komchen, name='komchen'),
    

]

