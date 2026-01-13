from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('callback/', views.spotify_callback, name='spotify_callback'),
    path('login/', views.spotify_login, name="spotify_login"),
    path('result/', views.result, name="result"),
    path('refresh/', views.refresh_top, name="refresh_top"),
]