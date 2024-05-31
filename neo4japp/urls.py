# myapp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # The home page
    path('Resultat/', views.display_map, name='display_map'),
    path('', views.display_mapHome, name='display_maphomr'),

    # Matches any html file
]
