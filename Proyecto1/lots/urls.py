from django.urls import path
from . import views

urlpatterns = [
  
    path("api/<slug:development_slug>/etapa/<int:stage_number>/lots.json",
         views.lots_json, name="lots_json"),
    path("<slug:development_slug>/etapa/<int:stage_number>/lote/<slug:lot_code>/",
         views.lot_detail, name="lot_detail"),
]
