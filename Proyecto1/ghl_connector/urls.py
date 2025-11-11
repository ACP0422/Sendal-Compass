from django.urls import path
from . import views

urlpatterns = [
    path("lots/", views.api_lots, name="lots"),
]
