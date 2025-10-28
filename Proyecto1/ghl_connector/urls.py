from django.urls import path
from . import views

urlpatterns = [
    path("lead/create/", views.create_lead, name="create_lead"),
    path('api/lot/upsert/', views.lot_upsert, name='lot_upsert')
]
