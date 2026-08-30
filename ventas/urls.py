from django.urls import path

from .api.views import ComprarPaseAPIView, EventoListAPIView
from .views import CatalogoView, ComprarPaseView, EventoDetalleView

urlpatterns = [
    path('', CatalogoView.as_view(), name='catalogo'),
    path('evento/<int:evento_id>/', EventoDetalleView.as_view(), name='evento_detalle'),
    path('comprar/<int:evento_id>/', ComprarPaseView.as_view(), name='comprar_pase'),
    path('api/v1/eventos/', EventoListAPIView.as_view(), name='api_eventos'),
    path('api/v1/comprar/', ComprarPaseAPIView.as_view(), name='api_comprar'),
]
