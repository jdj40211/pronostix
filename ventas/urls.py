from django.urls import path

from .views import CatalogoView, ComprarPaseView, EventoDetalleView

urlpatterns = [
    path('', CatalogoView.as_view(), name='catalogo'),
    path('evento/<int:evento_id>/', EventoDetalleView.as_view(), name='evento_detalle'),
    path('comprar/<int:evento_id>/', ComprarPaseView.as_view(), name='comprar_pase'),
]
