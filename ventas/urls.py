from django.urls import path

from .views import CatalogoView, ComprarPaseView

urlpatterns = [
    path('', CatalogoView.as_view(), name='catalogo'),
    path('comprar/<int:evento_id>/', ComprarPaseView.as_view(), name='comprar_pase'),
]
