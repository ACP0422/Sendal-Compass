from django.urls import path
from . import views

app_name = "lots"

urlpatterns = [
    path("<slug:project_slug>/lots.json", views.lots_json, name="lots_json"),
    path("<slug:project_slug>/lot/<int:number>/", views.lot_detail_modal, name="lot_detail_modal"),
]
