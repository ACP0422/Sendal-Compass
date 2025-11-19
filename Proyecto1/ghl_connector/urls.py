from django.urls import path
from . import views
from principal.views import quote_lot

urlpatterns = [
    path("lots/", views.api_lots, name="lots"),
    path("quote-lot/", quote_lot, name="quote_lot"),
]
